# 製藥分析平台 · Pharma Analytics Platform

> **Architecture v6 · Phase 1a**  
> 讓藥廠各端的人（R&D、製程、QC、QA）都能取得資料，包含 Engineering Run / PPQ / Commercial Run 的完整脈絡，前處理、分析、建模都有足夠彈性可以自訂，分析結果能輸出為報告、Dashboard 或自動化模型服務。

---

## 快速開始

```bash
# 安裝依賴
pip install -r requirements.txt

# 啟動
streamlit run app/main.py
```

開啟瀏覽器至 **http://localhost:8501**

---

## 功能（Phase 1a）

### 📁 資料上傳
- 支援 CSV / Excel（.csv、.xlsx、.xls）
- 多編碼自動偵測（UTF-8、Big5、GBK 等）
- 上傳時選擇 `run_type`，由系統注入，不從檔案讀取
- 彈性欄位對應 UI，將來源欄位映射至 Canonical 欄位
- 驗證後預覽，確認無誤再寫入

### 🗂️ 資料庫瀏覽
- 依 Shape 類型、run_type、日期篩選
- 任意筆資料展開預覽（前 20 行）
- 支援刪除（含二次確認）

---

## Canonical Shape

所有資料進入平台後統一以兩種 Shape 儲存：

| Shape | 格式 | 必填欄位 |
|-------|------|---------|
| **BatchWide** | 每批次一行（wide） | `batch_id`、`run_type` |
| **TimeSeries** | 每時間點一行（wide） | `batch_id`、`run_type`、`timestamp` |

### run_type 種類

```
engineering_run  /  ppq_run  /  commercial_run  /  stability_run  /  validation_run
```

---

## 目錄結構

```
├── app/
│   ├── main.py                  # 首頁（平台狀態 + 導航）
│   └── pages/
│       ├── 1_upload.py          # 資料上傳頁
│       └── 2_data_library.py    # 資料庫瀏覽頁
├── core/
│   ├── connector/
│   │   ├── file_parser.py       # CSV / Excel 解析
│   │   └── column_mapper.py     # 欄位對應邏輯
│   ├── shapes/
│   │   ├── base.py              # RunType enum、UploadMetadata
│   │   ├── batch_wide.py        # BatchWide 驗證
│   │   └── time_series.py       # TimeSeries 驗證
│   └── store/
│       └── parquet_store.py     # Parquet 讀寫 + manifest.json
├── data/                        # gitignore — 本地資料，不納入版控
│   ├── canonical/
│   │   ├── batch_wide/
│   │   └── time_series/
│   └── manifest.json
├── PLAN.md                      # 端到端架構計劃書
├── PROJECT_STATUS.md            # 模組說明與現況
└── requirements.txt
```

---

## 依賴套件

| 套件 | 用途 |
|------|------|
| `streamlit` | Web UI |
| `pandas` | 資料處理 |
| `openpyxl` | Excel 讀取 |
| `pyarrow` | Parquet 讀寫 |
| `pydantic` | 資料驗證 |

---

## Phase 路線圖

| Phase | 內容 | 狀態 |
|-------|------|------|
| **1a** | CSV/Excel 手動上傳、BatchWide + TimeSeries、本地 Parquet | ✅ 完成 |
| **1b** | LIMS / MES / BMS Connector、Dagster 排程、OpenLineage、SPC 套件 | 🔜 規劃中 |
| **2** | ERP / OPC UA / 串流、CPV Dashboard、Model Serving | 🔜 規劃中 |
| **3** | GMP Validated、電子簽章（21 CFR Part 11）、CAPA Export | 🔜 規劃中 |

詳細架構請參閱 [PLAN.md](PLAN.md)。
