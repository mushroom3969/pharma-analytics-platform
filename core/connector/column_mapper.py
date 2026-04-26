from __future__ import annotations

import pandas as pd


def build_mapping_options(df: pd.DataFrame) -> list[str]:
    """Return column names available for mapping, with a blank sentinel for 'not mapped'."""
    return ["（不對應）"] + list(df.columns)


def apply_mapping(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """
    Rename source columns to canonical names based on mapping.
    mapping: {canonical_name: source_column_name}
    Source columns not included in mapping values are kept as-is.
    """
    sentinel = "（不對應）"
    rename = {v: k for k, v in mapping.items() if v and v != sentinel and v in df.columns}
    return df.rename(columns=rename)
