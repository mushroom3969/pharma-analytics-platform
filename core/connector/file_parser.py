from __future__ import annotations

import io

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def parse_file(uploaded_file) -> pd.DataFrame:
    """
    Parse a Streamlit UploadedFile (CSV or Excel) into a DataFrame.
    Returns the raw DataFrame with original column names preserved.
    """
    name: str = uploaded_file.name.lower()
    raw = uploaded_file.read()

    if name.endswith(".csv"):
        for encoding in ("utf-8", "utf-8-sig", "big5", "gbk", "latin1"):
            try:
                df = pd.read_csv(io.BytesIO(raw), encoding=encoding)
                return df
            except UnicodeDecodeError:
                continue
        raise ValueError("CSV 檔案編碼無法識別，請另存為 UTF-8 後重試。")

    if name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(raw), engine="openpyxl" if name.endswith(".xlsx") else None)
        return df

    raise ValueError(f"不支援的檔案格式。支援：{', '.join(sorted(SUPPORTED_EXTENSIONS))}")
