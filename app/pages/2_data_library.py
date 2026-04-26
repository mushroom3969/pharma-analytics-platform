from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.shapes.base import RunType
from core.store.parquet_store import delete_upload, list_uploads, load_shape

st.set_page_config(page_title="資料庫", page_icon="🗂️", layout="wide")
st.title("🗂️ Canonical Shape Store")
st.caption("所有已上傳資料的索引。下游分析只從這裡讀取資料。")

uploads = list_uploads()

if not uploads:
    st.info("目前尚無上傳記錄。請前往「資料上傳」頁面新增資料。")
    st.stop()

# ── 篩選 ────────────────────────────────────────────────────────────────────

col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    filter_shape = st.multiselect(
        "Shape 類型",
        options=["batch_wide", "time_series"],
        default=["batch_wide", "time_series"],
        format_func=lambda x: "BatchWide" if x == "batch_wide" else "TimeSeries",
    )

with col_f2:
    filter_run = st.multiselect(
        "run_type",
        options=[r.value for r in RunType],
        default=[r.value for r in RunType],
    )

with col_f3:
    dates = [u.uploaded_at.date() for u in uploads]
    date_range = st.date_input(
        "上傳日期範圍",
        value=(min(dates), max(dates)),
    )

filtered = [
    u for u in uploads
    if u.shape_type in filter_shape
    and u.run_type in filter_run
    and (
        len(date_range) < 2
        or (date_range[0] <= u.uploaded_at.date() <= date_range[1])
    )
]

st.caption(f"顯示 {len(filtered)} / {len(uploads)} 筆記錄")
st.divider()

# ── 表格列表 ────────────────────────────────────────────────────────────────

if not filtered:
    st.warning("沒有符合篩選條件的記錄。")
    st.stop()

for meta in sorted(filtered, key=lambda u: u.uploaded_at, reverse=True):
    shape_label = "BatchWide" if meta.shape_type == "batch_wide" else "TimeSeries"
    with st.expander(
        f"**{meta.filename}**　`{meta.run_type}`　{shape_label}　{meta.row_count} 行　"
        f"{meta.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')}",
        expanded=False,
    ):
        col_info, col_action = st.columns([4, 1])

        with col_info:
            st.text(f"upload_id : {meta.upload_id}")
            st.text(f"路徑      : {meta.parquet_path}")
            if meta.column_map:
                st.text("欄位對應  : " + "  |  ".join(f"{k}←{v}" for k, v in meta.column_map.items()))

            if st.button("載入資料預覽", key=f"load_{meta.upload_id}"):
                try:
                    df = load_shape(meta.parquet_path)
                    st.dataframe(df.head(20), use_container_width=True)
                except Exception as e:
                    st.error(f"讀取失敗：{e}")

        with col_action:
            if st.button("刪除", key=f"del_{meta.upload_id}", type="secondary"):
                st.session_state[f"confirm_{meta.upload_id}"] = True

            if st.session_state.get(f"confirm_{meta.upload_id}"):
                st.warning("確定要刪除？")
                if st.button("確認刪除", key=f"confirm_btn_{meta.upload_id}", type="primary"):
                    delete_upload(meta.upload_id)
                    st.session_state.pop(f"confirm_{meta.upload_id}", None)
                    st.success("已刪除。")
                    st.rerun()
                if st.button("取消", key=f"cancel_{meta.upload_id}"):
                    st.session_state.pop(f"confirm_{meta.upload_id}", None)
                    st.rerun()
