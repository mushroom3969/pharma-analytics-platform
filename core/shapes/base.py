from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal


class RunType(str, Enum):
    engineering_run = "engineering_run"
    ppq_run = "ppq_run"
    commercial_run = "commercial_run"
    stability_run = "stability_run"
    validation_run = "validation_run"


ShapeType = Literal["batch_wide", "time_series"]


@dataclass
class UploadMetadata:
    upload_id: str
    filename: str
    run_type: str
    shape_type: ShapeType
    uploaded_at: datetime
    row_count: int
    parquet_path: str
    column_map: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "upload_id": self.upload_id,
            "filename": self.filename,
            "run_type": self.run_type,
            "shape_type": self.shape_type,
            "uploaded_at": self.uploaded_at.isoformat(),
            "row_count": self.row_count,
            "parquet_path": self.parquet_path,
            "column_map": self.column_map,
        }

    @classmethod
    def from_dict(cls, d: dict) -> UploadMetadata:
        return cls(
            upload_id=d["upload_id"],
            filename=d["filename"],
            run_type=d["run_type"],
            shape_type=d["shape_type"],
            uploaded_at=datetime.fromisoformat(d["uploaded_at"]),
            row_count=d["row_count"],
            parquet_path=d["parquet_path"],
            column_map=d.get("column_map", {}),
        )
