# AGENTS.md

## 溝通方式（重要）
- 以繁體中文、簡單易懂的方式說明，避免專業術語；必要時用括號解釋。
- 以「一步一步」的指令與重點摘要為主，方便非專業開發者理解。
- 不確定需求時，先提出最少的釐清問題；已授權事項由我自行決策。

## 專案目的
建立暫時性的上傳閘道（gateway），讓手機端可以上傳影像並存入 PACS。
現階段 PACS 不支援 DICOMweb，先用傳統 DICOM C-STORE；未來可切換到 DICOMweb，因此後端必須可插拔，且需提供停用/退場方案。

## 來源優先順序與決策規則
- `photo_pacs_PRD.md` 為最高優先級；目前為空，先以本文件與使用者需求為基準。
- 若 PRD 與本文件衝突，以 PRD 為準，並回頭更新本文件。
- 需要假設時，記錄在 `docs/assumptions.md`（含日期與理由）。
- 不可逆決策需記錄在 `docs/decisions/YYYYMMDD-topic.md`。

## 開發方法（SDD + TDD）
### SDD（規格驅動）
1. 先建立/更新規格文件：`specs/<feature>.md`。
2. 規格必須包含：
   - 問題
   - 目標
   - 非目標
   - 使用者流程
   - API 或契約
   - 資料模型
   - 錯誤處理
   - 安全與隱私
   - 驗收標準
   - 測試計畫

### TDD（測試驅動）
1. 針對每一條驗收標準，先寫「會失敗」的測試。
2. 寫最小可行程式碼讓測試通過。
3. 測試全綠後再重構（不改行為）。
4. 任何 Bug 都要補回歸測試。

### 開發流程（可重複循環）
規格 → 測試 → 實作 → 重構 → 文件更新 → 簡單煙霧測試

### 小技巧（簡單但有效）
- 一次只做一條驗收標準，避免大範圍改動。
- 先用 mock 或假資料跑通流程，再補真實整合。
- 測試命名清楚對應驗收標準，出錯時容易定位。
- 重構時不改行為，只整理可讀性與重複邏輯。

## 基礎技術棧（除非 PRD 指示不同）
- Python 3.11
- FastAPI（HTTP gateway）
- pydicom + pynetdicom（DICOM 轉換與 C-STORE）
- httpx（DICOMweb STOW-RS / HIS API 客戶端）
- pytest（測試）
- ruff、black（靜態檢查與格式化）
- 本機檔案系統（暫存上傳檔與 DICOM）
- Docker Compose（部署）
- Cloudflare Tunnel（外網 HTTPS 存取）

## 架構規則
- 上傳 API 要穩定，後端可插拔（C-STORE 現在、DICOMweb 未來）。
- 分離責任：API、轉檔、PACS 傳輸、暫存。
- 外部系統以介面包裝，測試時可替換為假物件（test double）。
- 設定以環境變數為主，集中到單一 settings 模組。

## 安全與隱私
- 影像與中繼資料皆視為 PHI。
- 儘量減少保存時間；日誌避免記錄 PHI，必要時要遮罩或雜湊。
- 有條件時使用 TLS（對客戶端與 PACS 連線）。
- 每個請求要有 Request ID 以利稽核。

## 品質門檻
- 測試通過且覆蓋率符合規格。
- API 變更需同步更新規格與 README。
- 手動煙霧測試：上傳 → 轉 DICOM → 送 PACS（或 mock）。

## 完成定義（Definition of Done）
- 驗收標準以測試驗證通過。
- 文件更新完成（規格、runbook、假設、決策）。
- 基本可觀測性：結構化日誌與錯誤指標。

## 部署方式
- Docker Compose 包含兩個服務：`photo_pacs`（app）與 `cloudflared`（Cloudflare Tunnel）
- app port：`9470`，Cloudflare Tunnel Public Hostname 指向 `http://photo_pacs:9470`
- `cloudflared` 等 app 健康檢查通過後才啟動
- `.env` 控制所有環境變數，`.env.example` 提供分組範本

## 退場計畫
- 保留後端切換開關，並文件化如何停用 gateway（DICOMweb 上線後）。
- 切換步驟：將 `PHOTO_PACS_PACS_BACKEND` 改為 `dicomweb`，填入 DICOMweb URL，重啟即可。
