from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.connector.column_mapper import build_mapping_options
from core.connector.file_parser import parse_file
from core.shapes.base import RunType
from core.shapes.batch_wide import validate_batch_wide
from core.shapes.time_series import validate_time_series
from core.store.parquet_store import save_shape

st.set_page_config(page_title="資料上傳", page_icon="📁", layout="wide")
st.title("📁 CSV / Excel 資料上傳")
st.caption("Phase 1a · 手動上傳 · Canonical Shape Store")

# ── Step 1: 上傳檔案 ──────────────────────────────────────────────────────────

uploaded_file = st.file_uploader(
    "選擇或拖曳 CSV / Excel 檔案",
    type=["csv", "xlsx", "xls"],
    help="支援 .csv、.xlsx、.xls",
)

if uploaded_file is None:
    st.info("請先上傳檔案以繼續。")
    st.stop()

try:
    raw_df = parse_file(uploaded_file)
except ValueError as e:
    st.error(str(e))
    st.stop()

st.success(f"已解析：**{uploaded_file.name}**　共 {len(raw_df)} 行 × {len(raw_df.columns)} 欄")

with st.expander("原始資料預覽（前 5 行）", expanded=True):
    st.dataframe(raw_df.head(5), use_container_width=True)

st.divider()

# ── Step 2: 選擇 Metadata ────────────────────────────────────────────────────

col_meta1, col_meta2 = st.columns(2)

with col_meta1:
    run_type_val = st.selectbox(
        "run_type（必填）",
        options=[r.value for r in RunType],
        help="所有資料必須帶有 run_type，由系統注入，不從檔案讀取。",
    )

with col_meta2:
    shape_type = st.selectbox(
        "Canonical Shape",
        options=["batch_wide", "time_series"],
        format_func=lambda x: "BatchWide（每批次一行）" if x == "batch_wide" else "TimeSeries（連續時序）",
    )

st.divider()

# ── Step 3: 欄位對應 ──────────────────────────────────────────────────────────

st.subheader("欄位對應")
st.caption("將原始欄位對應到 Canonical 欄位。未對應的欄位會自動保留為製程參數欄。")

options = build_mapping_options(raw_df)

if shape_type == "batch_wide":
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        map_batch_id = st.selectbox("batch_id *（必填）", options, key="bw_batch_id")
    with col_b:
        map_product = st.selectbox("product（選填）", options, key="bw_product")
    with col_c:
        map_start_date = st.selectbox("start_date（選填）", options, key="bw_start_date")
    with col_d:
        map_end_date = st.selectbox("end_date（選填）", options, key="bw_end_date")

    column_map = {
        "batch_id": map_batch_id,
        "product": map_product,
        "start_date": map_start_date,
        "end_date": map_end_date,
    }
else:
    col_a, col_b = st.columns(2)
    with col_a:
        map_batch_id = st.selectbox("batch_id *（必填）", options, key="ts_batch_id")
    with col_b:
        map_timestamp = st.selectbox("timestamp *（必填）", options, key="ts_timestamp")

    column_map = {
        "batch_id": map_batch_id,
        "timestamp": map_timestamp,
    }

sentinel = "（不對應）"
column_map = {k: v for k, v in column_map.items() if v != sentinel}

st.divider()

# ── Step 4: 驗證 + 預覽 ───────────────────────────────────────────────────────

preview_clicked = st.button("預覽轉換結果", type="secondary")

if preview_clicked or st.session_state.get("_preview_ok"):
    run_type = RunType(run_type_val)
    try:
        if shape_type == "batch_wide":
            preview_df = validate_batch_wide(raw_df.copy(), column_map, run_type)
        else:
            preview_df = validate_time_series(raw_df.copy(), column_map, run_type)

        st.session_state["_preview_ok"] = True
        st.session_state["_preview_df"] = preview_df
        st.session_state["_column_map"] = column_map

        st.success(f"驗證通過　→　{len(preview_df)} 行 × {len(preview_df.columns)} 欄")
        st.dataframe(preview_df.head(5), use_container_width=True)

    except ValueError as e:
        st.session_state["_preview_ok"] = False
        st.error(f"驗證失敗：{e}")
        st.stop()

st.divider()

# ── Step 5: 確認上傳 ──────────────────────────────────────────────────────────

if st.session_state.get("_preview_ok"):
    if st.button("確認上傳", type="primary"):
        meta = save_shape(
            df=st.session_state["_preview_df"],
            shape_type=shape_type,
            run_type=run_type_val,
            source_name=uploaded_file.name,
            column_map=st.session_state["_column_map"],
        )

        st.session_state["_preview_ok"] = False

        st.success(
            f"上傳成功！\n\n"
            f"**upload_id**: `{meta.upload_id}`\n\n"
            f"**Shape**: {meta.shape_type}　**run_type**: {meta.run_type}\n\n"
            f"**行數**: {meta.row_count}　**路徑**: `{meta.parquet_path}`"
        )
else:
    st.button("確認上傳", type="primary", disabled=True, help="請先點擊「預覽轉換結果」並確認無誤。")
