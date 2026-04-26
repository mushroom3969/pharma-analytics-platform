# 專案現況說明

**Pharma Analytics Platform · Phase 1a · 最後更新：2026-04-26**

---

## 目前完成的功能

### Phase 1a｜CSV / Excel 手動上傳

使用者（R&D / 製程 / QC / QA）可透過 Web UI 上傳批次資料檔案，系統自動附加 `run_type` metadata 並轉換為 Canonical Shape 後存入本地 Canonical Shape Store（Parquet 格式）。

**啟動方式：**
```bash
pip install -r requirements.txt
streamlit run app/main.py
# 開啟 http://localhost:8501
```

---

## 目錄結構

```
Manufacture Analysis Project/
├── app/
│   ├── main.py                  # Streamlit 首頁（平台狀態 + 導航）
│   └── pages/
│       ├── 1_upload.py          # 上傳頁（5 步驟流程）
│       └── 2_data_library.py    # 資料庫瀏覽頁
│
├── core/
│   ├── connector/
│   │   ├── file_parser.py       # CSV / Excel 解析（多編碼自動偵測）
│   │   └── column_mapper.py     # 欄位對應邏輯
│   ├── shapes/
│   │   ├── base.py              # RunType enum、UploadMetadata dataclass
│   │   ├── batch_wide.py        # BatchWide 驗證與轉換
│   │   └── time_series.py       # TimeSeries 驗證與轉換
│   └── store/
│       └── parquet_store.py     # Parquet 讀寫 + manifest.json 維護
│
├── data/
│   ├── canonical/
│   │   ├── batch_wide/          # {run_type}/{timestamp}_{name}.parquet
│   │   └── time_series/         # {run_type}/{timestamp}_{name}.parquet
│   └── manifest.json            # 上傳歷史索引
│
├── requirements.txt
├── PLAN.md                      # 端到端架構計劃書
└── PROJECT_STATUS.md            # 本文件
```

---

## 各模組說明

### `core/shapes/base.py`

定義平台共用的基礎型別。

- **`RunType`（Enum）**：所有資料進平台前必須帶的標籤，共 5 種值：
  - `engineering_run`
  - `ppq_run`
  - `commercial_run`
  - `stability_run`
  - `validation_run`

- **`UploadMetadata`（dataclass）**：每次上傳的記錄，包含 `upload_id`、`filename`、`run_type`、`shape_type`、`uploaded_at`、`row_count`、`parquet_path`、`column_map`，可序列化為 dict / 從 dict 還原。

---

### `core/shapes/batch_wide.py`

**BatchWide Shape**：每一行代表一個批次（wide format）。

```
batch_id | run_type      | product | start_date | yield | pH  | temp_avg | ...
B001     | ppq_run       | Drug A  | 2024-01-10 | 95.2  | 7.1 | 25.3     | ...
B002     | ppq_run       | Drug A  | 2024-01-15 | 96.1  | 7.0 | 25.1     | ...
```

- **必填欄位**：`batch_id`（由使用者在欄位對應中指定來源欄）
- **系統注入**：`run_type`（使用者在 UI 選擇，不從檔案讀取）
- **選填識別欄**：`product`、`start_date`、`end_date`
- **參數欄**：其餘欄位原樣保留

函數：`validate_batch_wide(df, column_map, run_type) → pd.DataFrame`

---

### `core/shapes/time_series.py`

**TimeSeries Shape**：每一行代表一個批次在一個時間點的量測（wide format）。

```
batch_id | run_type         | timestamp           | temp  | pressure | pH  | ...
B001     | engineering_run  | 2024-01-10 08:00:00 | 25.3  | 1.2      | 7.1 | ...
B001     | engineering_run  | 2024-01-10 08:01:00 | 25.4  | 1.2      | 7.0 | ...
```

- **必填欄位**：`batch_id`、`timestamp`（由使用者指定來源欄）
- **系統注入**：`run_type`
- **參數欄**：其餘欄位原樣保留
- **自動排序**：依 `batch_id`、`timestamp` 升序排列

函數：`validate_time_series(df, column_map, run_type) → pd.DataFrame`

---

### `core/connector/file_parser.py`

```python
parse_file(uploaded_file) → pd.DataFrame
```

- 支援 `.csv`、`.xlsx`、`.xls`
- CSV 自動嘗試多種編碼：`utf-8` → `utf-8-sig` → `big5` → `gbk` → `latin1`
- Excel 使用 `openpyxl` 引擎

---

### `core/connector/column_mapper.py`

```python
build_mapping_options(df) → list[str]   # 返回欄位清單（含「不對應」選項）
apply_mapping(df, mapping) → pd.DataFrame
```

`mapping` 格式：`{"canonical_name": "source_column_name"}`
未指定對應的來源欄位原樣保留（歸為參數欄）。

---

### `core/store/parquet_store.py`

Canonical Shape Store 的讀寫介面。

| 函數 | 說明 |
|------|------|
| `save_shape(df, shape_type, run_type, source_name, column_map)` | 寫入 Parquet，更新 manifest.json，回傳 `UploadMetadata` |
| `list_uploads()` | 讀取 manifest.json，回傳所有上傳記錄 |
| `load_shape(parquet_path)` | 讀取指定 Parquet 檔案 |
| `delete_upload(upload_id)` | 刪除 Parquet 檔案並從 manifest.json 移除 |

**Parquet 路徑規則：**
```
data/canonical/{shape_type}/{run_type}/{YYYYMMDD_HHMMSS}_{source_name}.parquet
```

**manifest.json 格式：**
```json
[
  {
    "upload_id": "uuid4",
    "filename": "batch_report.xlsx",
    "run_type": "ppq_run",
    "shape_type": "batch_wide",
    "uploaded_at": "2024-04-26T14:30:22",
    "row_count": 24,
    "parquet_path": "data/canonical/batch_wide/ppq_run/20240426_143022_batch_report.parquet",
    "column_map": {"batch_id": "Batch", "product": "Product Name"}
  }
]
```

---

### `app/pages/1_upload.py`｜上傳頁

**5 步驟上傳流程：**

```
步驟 1  上傳檔案       → 解析 CSV/Excel，顯示原始欄位與前 5 行預覽
步驟 2  選擇 Metadata  → run_type（下拉，5 種）、Shape 類型（BatchWide / TimeSeries）
步驟 3  欄位對應       → 指定哪個來源欄位對應到 batch_id（必填）、
                        timestamp（TimeSeries 必填）、product / start_date / end_date（選填）
步驟 4  驗證 + 預覽    → 點「預覽轉換結果」，顯示轉換後前 5 行；驗證失敗以錯誤訊息提示
步驟 5  確認上傳       → 點「確認上傳」，寫入 Parquet + 更新 manifest.json；顯示 upload_id 與路徑
```

---

### `app/pages/2_data_library.py`｜資料庫瀏覽頁

- 讀取 manifest.json，以卡片展開列表顯示所有上傳記錄
- **篩選**：Shape 類型、run_type、上傳日期範圍
- **預覽**：點「載入資料預覽」顯示前 20 行
- **刪除**：含二次確認（避免誤刪）

---

### `app/main.py`｜首頁

- 顯示平台目前狀態指標（BatchWide / TimeSeries 資料集數量、總上傳記錄）
- 顯示各 Phase 進度
- 快速導航連結至上傳頁 / 資料庫頁

---

## Phase 完成定義

### Phase 1a（目前）✅

- [x] 可上傳 CSV / Excel（含多編碼自動偵測）
- [x] run_type 由系統注入，5 種值可選，不從原始檔案讀取
- [x] 欄位對應 UI 正確運作（BatchWide & TimeSeries 動態切換）
- [x] 資料存為 Parquet，路徑按 shape_type / run_type 分類
- [x] manifest.json 維護完整上傳歷史（含 column_map 記錄）
- [x] 資料庫瀏覽頁可查看、預覽、刪除上傳記錄

### Phase 1b（下一步）🔜

- [ ] LIMS Connector（LabWare / STARLIMS）
- [ ] MES Connector（SAP ME / Rockwell Plex）
- [ ] BMS Connector（環境監控）
- [ ] Batch Connector via Dagster（定時排程）
- [ ] OpenLineage 全流程追蹤
- [ ] Report 生成（Jinja2 + WeasyPrint → PDF）
- [ ] SPC + 製程能力基礎套件

---

## 依賴套件

```
streamlit>=1.32     # Web UI
pandas>=2.0         # 資料處理
openpyxl>=3.1       # Excel 讀取
pyarrow>=15.0       # Parquet 讀寫
pydantic>=2.0       # 資料驗證（未來 Shape 正式 model 用）
```
