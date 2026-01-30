# Runbook（操作手冊）

## 啟動
1. 安裝套件：`pip install -e .[dev]`
2. 設定 `.env`（參考 `.env.example`）
3. 啟動服務：`uvicorn photo_pacs.main:app --reload`

## Docker Compose 啟動
1. 複製 `.env.example` 成 `.env` 並設定參數
2. 啟動：`docker compose up -d --build`
3. 進入 `http://<主機IP>:8000`

## 手動煙霧測試
1. 開啟 `http://127.0.0.1:8000`，進入 PWA。
2. 選擇至少一張影像、填入 PatientID 或病歷號。
3. 點「PACS 送信」，確認顯示成功。
4. 到「設定」頁測試 C-ECHO。

## 常見錯誤排除
- `VALIDATION_ERROR`：欄位缺漏或格式錯誤。
- `PATIENT_NOT_FOUND`：病歷號查不到（HIS 未命中）。
- `PATIENT_ID_MISMATCH`：PatientID 與病歷號查回不一致。
- `HIS_UNAVAILABLE`：HIS 連線失敗或未設定 Base URL。
- `PACS_TIMEOUT` / `PACS_REJECTED`：PACS 連線問題。

## 退場
1. 切換後端為 DICOMweb 新系統。
2. 停止 gateway 服務並清理 `data/` 暫存。
