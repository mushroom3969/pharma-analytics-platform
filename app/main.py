from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.store.parquet_store import list_uploads
from core.store.product_store import list_products

st.set_page_config(
    page_title="製藥分析平台",
    page_icon="💊",
    layout="wide",
)

st.title("💊 製藥分析平台")
st.caption("Pharma Analytics Platform · Architecture v6 · Phase 1a")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("平台狀態")
    uploads = list_uploads()
    batch_wide_count = sum(1 for u in uploads if u.shape_type == "batch_wide")
    ts_count = sum(1 for u in uploads if u.shape_type == "time_series")
    product_count = len(list_products())

    st.metric("BatchWide 資料集", batch_wide_count)
    st.metric("TimeSeries 資料集", ts_count)
    st.metric("總上傳記錄", len(uploads))
    st.metric("Products", product_count)

with col2:
    st.subheader("目前 Phase")

    phases = {
        "Phase 1a · CSV/Excel 手動上傳": "✅ 已完成",
        "Phase 1b · LIMS / MES Connector": "🔜 規劃中",
        "Phase 2 · ERP / OPC UA / 串流": "🔜 規劃中",
        "Phase 3 · GMP 驗證 / 電子簽章": "🔜 規劃中",
    }

    for phase, status in phases.items():
        st.write(f"{status}　{phase}")

st.divider()

st.subheader("快速導航")
st.page_link("pages/1_upload.py", label="📁 上傳資料", icon="📁")
st.page_link("pages/2_data_library.py", label="🗂️ 資料庫", icon="🗂️")
st.page_link("pages/3_products.py", label="📦 Products", icon="📦")

st.divider()
st.caption(
    "設計目標：讓藥廠各端的人（R&D、製程、QC、QA）都能取得資料，"
    "包含 Engineering Run / PPQ / Commercial Run 的完整脈絡。"
)
