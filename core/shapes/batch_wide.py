from __future__ import annotations

import pandas as pd

from .base import RunType


REQUIRED_FIELDS = ["batch_id"]
OPTIONAL_IDENTITY_FIELDS = ["product", "start_date", "end_date"]


def validate_batch_wide(
    df: pd.DataFrame,
    column_map: dict,
    run_type: RunType,
) -> pd.DataFrame:
    """
    Apply column mapping, inject run_type, and validate BatchWide constraints.

    column_map keys: canonical field names (batch_id, product, ...)
    column_map values: source column names from the uploaded file
    """
    result = df.copy()

    rename = {v: k for k, v in column_map.items() if v and v in result.columns}
    result = result.rename(columns=rename)

    mapped_canonical = set(column_map.keys())
    unmapped_source = [c for c in result.columns if c not in mapped_canonical]

    result = result[[c for c in result.columns if c not in unmapped_source] + unmapped_source]

    if "batch_id" not in result.columns:
        raise ValueError("batch_id 欄位未對應，無法建立 BatchWide Shape。")

    null_batch = result["batch_id"].isna().sum()
    if null_batch > 0:
        raise ValueError(f"batch_id 有 {null_batch} 筆空值，請確認欄位內容。")

    result["run_type"] = run_type.value if isinstance(run_type, RunType) else run_type

    cols = ["batch_id", "run_type"]
    for opt in OPTIONAL_IDENTITY_FIELDS:
        if opt in result.columns:
            cols.append(opt)
    param_cols = [c for c in result.columns if c not in cols]
    result = result[cols + param_cols]

    return result
