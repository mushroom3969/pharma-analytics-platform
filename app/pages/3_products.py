from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.store.parquet_store import list_uploads, load_shape
from core.store.product_store import (
    create_product,
    delete_product,
    list_products,
    save_product,
)

st.set_page_config(
    page_title="Products | Pharma Analytics",
    page_icon="📦",
    layout="wide",
)

st.title("📦 Product Library")

# ── Session state ─────────────────────────────────────────────────────────────
if "selected_pid" not in st.session_state:
    st.session_state.selected_pid = None
if "confirm_delete_product" not in st.session_state:
    st.session_state.confirm_delete_product = False

products = list_products()

# ── Sidebar: product list + create ────────────────────────────────────────────
with st.sidebar:
    st.subheader("產品列表")

    with st.form("new_product_form", clear_on_submit=True):
        new_name = st.text_input("產品名稱", placeholder="e.g. Drug A")
        if st.form_submit_button("＋ 新增產品", use_container_width=True):
            if new_name.strip():
                p = create_product(new_name.strip())
                st.session_state.selected_pid = p.product_id
                st.session_state.confirm_delete_product = False
                st.rerun()

    st.divider()

    if not products:
        st.info("尚無產品，請新增。")
    else:
        for p in products:
            is_sel = st.session_state.selected_pid == p.product_id
            label = f"→ {p.name}" if is_sel else p.name
            if st.button(label, key=f"sel_{p.product_id}", use_container_width=True):
                st.session_state.selected_pid = p.product_id
                st.session_state.confirm_delete_product = False
                st.rerun()

# ── Main area ─────────────────────────────────────────────────────────────────
if st.session_state.selected_pid is None:
    st.info("← 從左側選擇一個產品，或新增產品。")
    st.stop()

product = next((p for p in products if p.product_id == st.session_state.selected_pid), None)
if product is None:
    st.session_state.selected_pid = None
    st.rerun()

# Header row
col_title, col_del = st.columns([6, 1])
with col_title:
    st.subheader(f"📦 {product.name}")
    st.caption(f"建立時間：{product.created_at}　｜　ID：{product.product_id[:8]}…")

with col_del:
    st.write("")
    st.write("")
    if not st.session_state.confirm_delete_product:
        if st.button("🗑️ 刪除", type="secondary", use_container_width=True):
            st.session_state.confirm_delete_product = True
            st.rerun()
    else:
        st.warning(f"確認刪除 **{product.name}**？")
        if st.button("確認刪除", type="primary", use_container_width=True):
            delete_product(product.product_id)
            st.session_state.selected_pid = None
            st.session_state.confirm_delete_product = False
            st.rerun()
        if st.button("取消", use_container_width=True):
            st.session_state.confirm_delete_product = False
            st.rerun()

# Rename
with st.form("rename_form"):
    col_in, col_btn = st.columns([5, 1])
    with col_in:
        renamed = st.text_input("重新命名", value=product.name, label_visibility="collapsed")
    with col_btn:
        if st.form_submit_button("重新命名", use_container_width=True):
            if renamed.strip() and renamed.strip() != product.name:
                product.name = renamed.strip()
                save_product(product)
                st.rerun()

st.divider()

# ── Sub-items ─────────────────────────────────────────────────────────────────
st.subheader("子項 Sub-items")

for category in list(product.sub_items.keys()):
    count = len(product.sub_items[category])
    with st.expander(f"**{category}**　（{count} 項）", expanded=True):
        values = product.sub_items[category]

        # Existing values — each as a removable chip button
        if values:
            chip_cols = st.columns(min(len(values), 5))
            for i, val in enumerate(values):
                with chip_cols[i % 5]:
                    if st.button(
                        f"✕  {val}",
                        key=f"rm_{category}_{i}",
                        help="點擊移除此值",
                        use_container_width=True,
                    ):
                        product.sub_items[category].pop(i)
                        save_product(product)
                        st.rerun()
        else:
            st.caption("（尚無項目）")

        # Add a value
        with st.form(f"add_val_{category}", clear_on_submit=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                add_val = st.text_input(
                    "add",
                    placeholder=f"新增 {category} 值…",
                    label_visibility="collapsed",
                )
            with c2:
                if st.form_submit_button("新增", use_container_width=True):
                    v = add_val.strip()
                    if v and v not in product.sub_items[category]:
                        product.sub_items[category].append(v)
                        save_product(product)
                        st.rerun()

        # Remove entire category
        if st.button(
            f"移除「{category}」整個類別",
            key=f"rm_cat_{category}",
            type="secondary",
        ):
            del product.sub_items[category]
            save_product(product)
            st.rerun()

# Add custom category
st.write("")
with st.expander("＋ 新增子項類別", expanded=False):
    with st.form("new_cat_form", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            new_cat = st.text_input(
                "類別名稱",
                placeholder="e.g. regulatory_region、container_type…",
                label_visibility="collapsed",
            )
        with c2:
            if st.form_submit_button("建立", use_container_width=True):
                cat_key = new_cat.strip()
                if cat_key and cat_key not in product.sub_items:
                    product.sub_items[cat_key] = []
                    save_product(product)
                    st.rerun()

# ── Associated Batches ────────────────────────────────────────────────────────
st.divider()
st.subheader("關聯批次 Associated Batches")

matched_rows: list[pd.DataFrame] = []
for u in list_uploads():
    if u.shape_type != "batch_wide":
        continue
    try:
        df = load_shape(u.parquet_path)
        if "product" in df.columns:
            hits = df[df["product"].astype(str) == product.name]
            if not hits.empty:
                matched_rows.append(hits)
    except Exception:
        pass

if matched_rows:
    combined = pd.concat(matched_rows, ignore_index=True)
    st.dataframe(combined, use_container_width=True)
    st.caption(f"共 {len(combined)} 筆批次資料（來源：BatchWide Canonical Store）")
else:
    st.info(
        f"尚無 BatchWide 資料的 product 欄位對應到「{product.name}」。\n\n"
        "上傳 BatchWide 資料時，在欄位對應中指定 product 欄位，即可在此自動顯示關聯批次。"
    )
