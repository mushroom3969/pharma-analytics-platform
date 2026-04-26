from __future__ import annotations

import pandas as pd

from .base import RunType


def validate_time_series(
    df: pd.DataFrame,
    column_map: dict,
    run_type: RunType,
) -> pd.DataFrame:
    """
    Apply column mapping, inject run_type, and validate TimeSeries constraints.

    column_map keys: canonical field names (batch_id, timestamp, ...)
    column_map values: source column names from the uploaded file
    """
    result = df.copy()

    rename = {v: k for k, v in column_map.items() if v and v in result.columns}
    result = result.rename(columns=rename)

    if "batch_id" not in result.columns:
        raise ValueError("batch_id 欄位未對應，無法建立 TimeSeries Shape。")
    if "timestamp" not in result.columns:
        raise ValueError("timestamp 欄位未對應，TimeSeries Shape 需要時間戳記。")

    null_batch = result["batch_id"].isna().sum()
    if null_batch > 0:
        raise ValueError(f"batch_id 有 {null_batch} 筆空值，請確認欄位內容。")

    try:
        result["timestamp"] = pd.to_datetime(result["timestamp"])
    except Exception:
        raise ValueError("timestamp 欄位無法解析為時間格式，請確認欄位內容。")

    null_ts = result["timestamp"].isna().sum()
    if null_ts > 0:
        raise ValueError(f"timestamp 有 {null_ts} 筆無法解析的值。")

    result["run_type"] = run_type.value if isinstance(run_type, RunType) else run_type

    cols = ["batch_id", "run_type", "timestamp"]
    param_cols = [c for c in result.columns if c not in cols]
    result = result[cols + param_cols]

    result = result.sort_values(["batch_id", "timestamp"]).reset_index(drop=True)

    return result
