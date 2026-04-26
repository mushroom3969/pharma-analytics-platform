from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd

from core.shapes.base import ShapeType, UploadMetadata

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "canonical"
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifest.json"


def _ensure_dirs():
    (DATA_DIR / "batch_wide").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "time_series").mkdir(parents=True, exist_ok=True)


def save_shape(
    df: pd.DataFrame,
    shape_type: ShapeType,
    run_type: str,
    source_name: str,
    column_map: dict | None = None,
) -> UploadMetadata:
    _ensure_dirs()

    safe_name = Path(source_name).stem.replace(" ", "_")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}_{safe_name}.parquet"

    run_dir = DATA_DIR / shape_type / run_type
    run_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = run_dir / filename

    df.to_parquet(parquet_path, index=False)

    meta = UploadMetadata(
        upload_id=str(uuid.uuid4()),
        filename=source_name,
        run_type=run_type,
        shape_type=shape_type,
        uploaded_at=datetime.now(),
        row_count=len(df),
        parquet_path=str(parquet_path.relative_to(PROJECT_ROOT)),
        column_map=column_map or {},
    )

    _append_manifest(meta)
    return meta


def list_uploads() -> list[UploadMetadata]:
    if not MANIFEST_PATH.exists():
        return []
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        records = json.load(f)
    return [UploadMetadata.from_dict(r) for r in records]


def load_shape(parquet_path: str) -> pd.DataFrame:
    full_path = PROJECT_ROOT / parquet_path
    return pd.read_parquet(full_path)


def delete_upload(upload_id: str) -> bool:
    uploads = list_uploads()
    target = next((u for u in uploads if u.upload_id == upload_id), None)
    if target is None:
        return False

    full_path = PROJECT_ROOT / target.parquet_path
    if full_path.exists():
        os.remove(full_path)

    remaining = [u for u in uploads if u.upload_id != upload_id]
    _write_manifest(remaining)
    return True


def _append_manifest(meta: UploadMetadata):
    uploads = list_uploads()
    uploads.append(meta)
    _write_manifest(uploads)


def _write_manifest(uploads: list[UploadMetadata]):
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump([u.to_dict() for u in uploads], f, ensure_ascii=False, indent=2)
