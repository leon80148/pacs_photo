# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 溝通語言

以繁體中文溝通，簡單易懂，避免不必要的專業術語。技術名詞保留原文。

## 專案概述

暫時性 PWA + Gateway，讓手機/平板拍照上傳後轉成 DICOM Secondary Capture 並透過 C-STORE 送入 PACS。未來 PACS 支援 DICOMweb 後可切換並停用此 gateway。

## 常用指令

```bash
# 安裝（含開發依賴）
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]

# 啟動開發伺服器（預設 mock 後端）
uvicorn photo_pacs.main:app --reload

# 啟動開發伺服器（區域網路可連線）
uvicorn photo_pacs.main:app --reload --host 0.0.0.0 --port 9470

# Docker 部署（含 Cloudflare Tunnel）
docker compose up -d --build

# 測試
pytest                          # 全部測試
pytest tests/test_studies.py    # 單一檔案
pytest tests/test_studies.py::test_create_study_success_multi_image  # 單一測試

# Lint 與格式化
ruff check .
ruff format .
black src/ tests/
```

## 架構

### 請求流程（POST /api/studies）

表單驗證 → 儲存上傳檔 → PIL 影像轉 DICOM Secondary Capture → C-STORE 送 PACS → 清除暫存 → 回應結果

### 可插拔後端（Strategy + Factory 模式）

PACS 後端透過 Protocol 定義介面，以 `PHOTO_PACS_PACS_BACKEND` 環境變數選擇實作：

- **PACS**: `mock` | `cstore` | `dicomweb`（dicomweb 尚未實作）
  - 介面: `src/photo_pacs/pacs/base.py`
  - 工廠: `src/photo_pacs/pacs/__init__.py` → `get_pacs_sender()`

### 關鍵模組

| 模組 | 職責 |
|------|------|
| `api/routes/studies.py` | 核心上傳端點：驗證、轉檔、送 PACS |
| `services/conversion.py` | PIL 影像 → pydicom Dataset（Secondary Capture） |
| `services/settings_store.py` | JSON 檔案持久化運行時設定 |
| `pacs/cstore.py` | pynetdicom C-ECHO/C-STORE 實作 |
| `settings.py` | Pydantic BaseSettings，所有環境變數（前綴 `PHOTO_PACS_`） |
| `middleware.py` | Request ID 產生、指標計數 |

### 前端

`web/` 目錄下的靜態 PWA（HTML/JS/CSS），由 FastAPI 掛載為 static files。無前端建置步驟。

設定頁面依 `pacs_backend` 自動顯示對應的連線卡片（C-STORE 或 DICOMweb），本機送信端與 DICOM 寫入收進「進階設定」摺疊區塊。

### 部署

- **Docker Compose**：`photo_pacs`（FastAPI app）+ `cloudflared`（Cloudflare Tunnel）
- Cloudflared 會等 app 健康檢查通過才啟動
- 預設 port：`9470`
- 外網存取透過 Cloudflare Tunnel（HTTPS），PWA 安裝與 Service Worker 可正常運作

## 開發方法論（SDD + TDD）

1. **測試先行**：針對驗收標準先寫失敗測試 → 最小實作通過 → 重構
2. **一次一條驗收標準**，避免大範圍改動

## 測試慣例

- 框架：pytest，設定在 `pyproject.toml`（testpaths=tests, pythonpath=src）
- `tests/conftest.py` 提供 `make_client` fixture，使用暫存目錄與 mock 後端
- 測試命名對應驗收標準，出錯時易定位

## 設定管理

- **靜態設定**：環境變數，前綴 `PHOTO_PACS_`，由 `settings.py` 的 Pydantic BaseSettings 解析
- **運行時設定**：`data/settings.json`，可透過 `PUT /api/settings` 即時修改 PACS 參數
- **後端模式查詢**：`GET /api/settings/info` 回傳 `{ "pacsBackend": "..." }`，前端據此切換 UI
- 參考 `.env.example` 取得完整變數清單（分組註解，不常改的參數預設註解掉）

## 安全與隱私

- 影像與中繼資料視為 PHI，日誌避免記錄 PHI
- 每個請求帶 Request ID（X-Request-ID）以利稽核
- 暫存檔案成功送出後自動刪除（除非 `KEEP_FILES_ON_SUCCESS=true`）

## 錯誤代碼對照

| HTTP | 錯誤碼 | 情境 |
|------|--------|------|
| 400 | VALIDATION_ERROR | 表單驗證失敗 |
| 502 | PACS_REJECTED | PACS 拒絕傳輸 |
| 504 | PACS_TIMEOUT | PACS 連線逾時 |
