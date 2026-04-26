# 製藥分析平台　端到端架構計劃書

**Pharma Analytics Platform · Architecture v6 · Final**

---

## 設計目標

讓藥廠各端的人（R&D、製程、QC、QA）都能取得資料，包含 Engineering Run / PPQ / Commercial Run 的完整脈絡，前處理、清洗、縮圖、分析、建模都有足夠彈性可以自訂，寫好的邏輯可以儲存、版控、供後續重複使用，分析結果能輸出為報告、Dashboard 或自動化模型服務。

---

## 核心設計原則

| 原則 | 說明 |
|------|------|
| **run_type 從第一天就必填** | `engineering_run / ppq_run / commercial_run / stability_run / validation_run`，防止不同性質批次混入分析 |
| **Connector Template 分離** | 工程師一次建立 Template，資料負責人自助設定 Instance，各部門自助接資料，不需每次找工程師 |
| **CPV 是核心貢獻** | FDA Stage 3 要求，自動化 CPV 最有可能收到藥廠真實採購預算的場景 |
| **Output 層完整閉環** | 分析 → Report → Dashboard → Model Serving → CAPA，每個結果都有對應使用路徑 |
| **三層邏輯累積路徑** | Script（個人暫存）→ Custom Step（可重用）→ Package（生產品質）→ GMP Validated，每步都有明確升級路徑 |

---

## 七層架構總覽

```
1. 資料來源層        CSV/Excel · LIMS · MES · BMS · ERP · OPC UA · 人員資料
        ↓
2. § 13 Connector 層  Batch / Event / Streaming Connector Template
        ↓
3. § 14 Preprocessing Pipeline 層  清洗 → 補值 → 單位轉換 → 欄位映射 → 跨來源 Join → 特徵工程
        ↓
4. Canonical Shape Store  TimeSeries · BatchWide · LabResult · BatchHierarchical · Genealogy
        ↓
5. § 18 四層分析框架   Descriptive → Diagnostic → Predictive → Prescriptive
        ↓
6. § 16 Output 層      Report · 即時業務 Dashboard · Model Serving · 電子簽章 · CAPA Export
        ↓
7. 合規 / Lineage 層   OpenLineage · Quarantine · 三層信任分級 · ALCOA+ · GMP 合規記錄
```

---

## 分層詳細說明

### 層 1｜資料來源層

> 所有資料進入平台前必須帶有 `run_type` 標籤。這個屬性從 Connector 層就確保注入，是所有下游分析正確過濾的前提。

| 資料源 | 系統 | Phase |
|--------|------|-------|
| **CSV / Excel 手動上傳** | 本地檔案 | **1a ✅** |
| LIMS | LabWare / STARLIMS | 1b |
| MES | SAP ME / Rockwell Plex | 1b–2 |
| 環境監控 (BMS) | 粒子計數 / 溫濕度 / 壓差 | 1b |
| ERP | SAP OData API | 2 |
| OPC UA Server | MES 已整合，非直連儀器 | 2 |
| 人員資料 | operator_id / 訓練狀態 | 2 |

> ⚠️ **直連儀器（SCADA/DCS）Phase 1–2 不建議。** 藥廠 OT/IT 網路分離，直連需要打通兩個網路，PoC 週期嚴重延長。Phase 2 改接 MES 已整合的 OPC UA Server，資料已有 batch context。

---

### 層 2｜§ 13 Connector 層

> 工程師一次性建立 **Connector Template**（連線邏輯），資料負責人透過 UI 填寫 **Connector Instance**（設定參數），不需要寫 code。Connector 執行時自動注入並驗證 run_type，不符合的資料進 DLQ。

| Connector | 說明 | Phase |
|-----------|------|-------|
| Batch Connector | 定時排程 / 手動觸發（Dagster） | 1b |
| Event Connector | 外部系統 Webhook POST | 2 |
| Streaming Connector | NATS bridge → OPC UA | 2 |

---

### 層 3｜§ 14 Preprocessing Pipeline 層

> 清洗 → 補值 → 單位轉換 → 欄位映射 → 跨來源 Join → 特徵工程。Pipeline 有版本管理，版本更新可對歷史資料重算確保一致性。每次執行記錄 OpenLineage。非工程師可透過視覺化 UI 組合內建 Step，不需寫 code。

**邏輯三層路徑：**

```
Workspace Script（個人暫存，不可重用）
    → Custom Step（清洗邏輯，可共用）
        → Package（生產品質，可合規）
            → GMP Validated（Phase 3）
```

---

### 層 4｜Canonical Shape Store

> 資料的唯一可信來源。所有下游分析從這裡取資料。每個 Shape 帶有 run_type 欄位，Package 執行時平台自動帶入對應的 run_type filter，防止不同性質批次混入分析。

| Shape | 說明 | Phase |
|-------|------|-------|
| **TimeSeries** | 連續時序資料 | **1a ✅** |
| **BatchWide** | 每批次一行，含 run_type 必填 | **1a ✅** |
| LabResult | 實驗室量測結果 | 1b |
| BatchHierarchical | ISA-88 對齊 | 2 |
| Genealogy | 批次譜系 | 3 |

---

### 層 5｜§ 18 四層分析框架

> 透過 §12 Analyst Workspace（探索）或 Package（生產品質執行）實作。每一層對應不同的問題類型與 run_type 組合。

| 層 | 問題 | 工具 |
|----|------|------|
| 一 Descriptive | 資料發生了什麼？ | 即時趨勢圖 / 批次對比 / 統計摘要 / BRR |
| 二 Diagnostic | 為什麼發生？ | SPC（Xbar-R/CUSUM/EWMA）/ Cpk/Ppk / MVA / RCA |
| 三 Predictive | 未來會發生什麼？ | ML 模型（回歸/RF/ANN）/ RTRt / 穩定性預測 |
| 四 Prescriptive | 應該做什麼？ | CAPA 閉環介面 / DOE 製程優化 / Digital Twin |

**§ 17 CPV 持續製程驗證模組（跨層一 + 層二，FDA Stage 3）**
只看 `commercial_run`。套件包：`cpv_control_chart / cpv_capability / cpv_trend / cpv_mvr / cpv_annual_report / cpv_alert`

---

### 層 6｜§ 16 Output 層：分析結果出口

| 出口 | 技術 | Phase |
|------|------|-------|
| Report 生成 | Jinja2 + WeasyPrint → PDF | 1b |
| 即時業務 Dashboard | Next.js + Plotly，訂閱 Shape Store | 2 |
| Model Serving | MLflow REST API，shadow deploy | 2 |
| 電子簽章 | 21 CFR Part 11（Keycloak） | 3 |
| CAPA Export | 偏差 → QMS 系統 | 3 |

---

### 層 7｜合規 / Lineage 層（橫切所有層）

> 從 Connector 到 Output，每一步都有 lineage 記錄。ALCOA+ 原則貫穿整個平台。三層信任分級（Community / Verified / Validated）確保套件品質。

| 元件 | 說明 | Phase |
|------|------|-------|
| OpenLineage | via Dagster，全流程追蹤 | 1b |
| Quarantine 機制 | 50 次門檻，7 天失效率 | 1b |
| 三層信任分級 | Community / Verified / Validated | 1b+ |
| ALCOA+ 合規 | Lineage store，可審計 | 2+ |
| GMP 合規記錄 | CSA 文件，IQ/OQ/PQ | 3 |

---

## Phase 路線圖

| Phase | 主要交付 | 狀態 |
|-------|----------|------|
| **1a** | CSV/Excel 手動上傳、BatchWide + TimeSeries Shape、本地 Parquet | ✅ 完成 |
| **1b** | LIMS/MES/BMS Connector、Batch Connector（Dagster）、OpenLineage、Report 生成、SPC + 製程能力套件 | 🔜 規劃中 |
| **2** | ERP/OPC UA/串流、完整 CPV Dashboard + 年度報告、Model Serving、即時業務 Dashboard | 🔜 規劃中 |
| **3** | GMP Validated tier、電子簽章（21 CFR Part 11）、CAPA Export、Digital Twin PoC | 🔜 規劃中 |

---

## 未來優化標記

| 項目 | 現況（Phase 1a） | 升級目標 |
|------|-----------------|---------|
| 🗄️ 儲存後端 | 本地 Parquet + manifest.json | DeltaLake / S3 + PostgreSQL metadata DB（Phase 2） |
| 🔌 Connector 層 | CSV/Excel 手動上傳 | 完整 Connector Template 機制，Dagster 排程（Phase 1b） |
| ✅ Schema 驗證 | 基本欄位存在檢查 | Pandera / Great Expectations + Quarantine DLQ（Phase 1b+） |
| 📊 Lineage 追蹤 | manifest.json 紀錄 | OpenLineage via Dagster（Phase 1b） |
| 🔐 認證權限 | 無登入機制 | Keycloak + 角色管理（Phase 3） |
| 🖥️ UI 框架 | Streamlit | Next.js + FastAPI（視 Phase 2+ 需求） |
