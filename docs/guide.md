# Photo PACS — 進階文件

基本安裝與使用請參考 [README](../README.md)。

## 目錄

- [架構](#架構)
- [使用教學（詳細版）](#使用教學詳細版)
- [環境變數](#環境變數)
- [API 文件](#api-文件)
- [本機開發](#本機開發)
- [專案結構](#專案結構)
- [測試](#測試)
- [錯誤代碼](#錯誤代碼)
- [常見問題](#常見問題)

---

## 架構

```
手機/平板（PWA）
    │
    ▼
Cloudflare Tunnel（HTTPS）    ← 外網存取（選用）
    │
    ▼
FastAPI Gateway（port 9470）
    │
    ├─ C-STORE ──▶ PACS 伺服器（傳統 DICOM port 104）
    │
    └─ DICOMweb ─▶ PACS 伺服器（STOW-RS over HTTPS）
```

- **C-STORE**：傳統 DICOM 協定，直接透過 TCP 連線。適合區網內的 PACS。
- **DICOMweb**：透過 HTTPS REST API（STOW-RS）。適合雲端 PACS 或需要穿越防火牆的場景。

透過 `.env` 的 `PHOTO_PACS_PACS_BACKEND` 切換模式，程式碼不用改。

---

## 使用教學（詳細版）

### 首頁：上傳影像

開啟網頁後會看到「首頁」頁面，分為幾個區塊：

#### 患者資訊

| 欄位 | 說明 | 必填 |
|------|------|------|
| 患者 ID | 例如 `A123456`，寫入 DICOM Patient ID | **是** |
| 患者姓名 | 寫入 DICOM Patient Name | 否 |
| 出生年月日 | 格式 `YYYY-MM-DD` | 否 |
| 性別 | 男 / 女 / 其他 / 未知 | 否 |

患者 ID 是唯一必填欄位。其他空白的話，DICOM 對應標籤會留空。

#### 檢查資訊

| 欄位 | 說明 |
|------|------|
| 模式 | **自動**（預設）＝送出時用當下時間；**手動**＝自己輸入日期時間 |
| 檢查日期時間 | 自動模式下鎖定，手動模式可選擇 |
| 檢查記述 | 自由文字，寫入 DICOM Study Description |

#### 影像

- 「**拍攝**」：開啟相機拍照
- 「**從相簿選擇**」：從相簿多選
- 每張照片有縮圖預覽，可個別刪除
- 支援 JPEG、PNG、BMP、WebP 等格式

#### 送出流程

填好患者 ID + 至少一張影像後，「**PACS 送信**」按鈕會亮起來。點擊後：

1. 影像上傳至 Gateway
2. 每張影像自動轉成 DICOM Secondary Capture
3. 同一批影像共用相同的 Study / Series Instance UID
4. 透過 C-STORE 或 DICOMweb 送入 PACS
5. 成功後表單自動清空

### 設定頁

切換到「設定」分頁，可即時修改連線參數，**不需重啟服務**。

#### PACS 連線（C-STORE 模式）

| 欄位 | 說明 | 範例 |
|------|------|------|
| 送信先 AET | PACS 的 AE Title | `PACS`、`DCM4CHEE` |
| 送信先 IP | PACS 伺服器 IP | `192.168.1.100` |
| 送信先 Port | PACS DICOM port | `104`、`11112` |

「**測試 C-ECHO**」按鈕可驗證連線。

#### DICOMweb 連線（DICOMweb 模式）

| 欄位 | 說明 | 範例 |
|------|------|------|
| Base URL | STOW-RS endpoint | `https://pacs.example.com/dcm4chee-arc/aets/DCM4CHEE/rs` |
| 驗證 TLS 證書 | 自簽憑證時可關閉 | 勾選 |
| 逾時秒數 | 請求逾時 | `30` |

設定頁會根據 `PACS_BACKEND` 自動只顯示對應的連線卡片。

#### 進階設定

展開「進階設定」可調整：

**本機送信端**：送信元 AET、Modality 代碼、影像長邊尺寸、Transfer Syntax、字元集

**DICOM 寫入旗標**：是否寫入患者資訊（ID 除外）、是否寫入檢查記述

#### 外觀

深色 / 淺色主題切換。

改完按「**儲存設定**」即可，設定存在 `data/settings.json`，立即生效。

---

## 環境變數

所有變數加上前綴 `PHOTO_PACS_`（Cloudflare Tunnel Token 除外）。

完整清單見 `.env.example`。

### 基本

| 變數 | 說明 | 預設 |
|------|------|------|
| `PACS_BACKEND` | PACS 後端模式（`mock` / `cstore` / `dicomweb`） | `mock` |
| `ENVIRONMENT` | 執行環境 | `dev` |

### 檔案路徑

| 變數 | 說明 | 預設 |
|------|------|------|
| `UPLOAD_DIR` | 上傳暫存目錄 | `data/uploads` |
| `DICOM_DIR` | DICOM 輸出目錄 | `data/dicom` |
| `SETTINGS_PATH` | 運行時設定檔路徑 | `data/settings.json` |
| `KEEP_FILES_ON_SUCCESS` | 成功後保留暫存檔 | `false` |
| `MAX_UPLOAD_MB` | 單檔上傳大小上限（MB） | `20` |

### C-STORE 模式

| 變數 | 說明 | 預設 |
|------|------|------|
| `PACS_HOST` | PACS 伺服器 IP | `127.0.0.1` |
| `PACS_PORT` | PACS port | `104` |
| `PACS_CALLED_AET` | 對方 AE Title | `PACS` |
| `LOCAL_CALLING_AET` | 本機 AE Title | `PHOTO_PACS` |

### C-STORE TLS（選用）

| 變數 | 說明 | 預設 |
|------|------|------|
| `PACS_TLS` | 啟用 TLS | `false` |
| `PACS_TLS_CA_FILE` | CA 憑證檔路徑 | （無） |
| `PACS_TLS_CERT_FILE` | 客戶端憑證檔路徑 | （無） |
| `PACS_TLS_KEY_FILE` | 客戶端金鑰檔路徑 | （無） |

### DICOMweb 模式

| 變數 | 說明 | 預設 |
|------|------|------|
| `DICOMWEB_BASE_URL` | STOW-RS Base URL | （無） |
| `DICOMWEB_VERIFY_TLS` | 驗證 TLS 證書 | `true` |
| `DICOMWEB_TIMEOUT_S` | 逾時秒數 | `30` |
| `DICOMWEB_AUTH_METHOD` | 認證方式（`none` / `basic` / `bearer`） | `none` |
| `DICOMWEB_USERNAME` | Basic 認證帳號 | （無） |
| `DICOMWEB_PASSWORD` | Basic 認證密碼 | （無） |
| `DICOMWEB_TOKEN` | Bearer Token | （無） |

### DICOM 影像參數

| 變數 | 說明 | 預設 |
|------|------|------|
| `LOCAL_MODALITY` | Modality 代碼 | `OT` |
| `LOCAL_RESIZE_MAX` | 影像長邊上限（px） | `1024` |
| `LOCAL_TRANSFER_SYNTAX` | Transfer Syntax UID | `1.2.840.10008.1.2` |
| `LOCAL_CHARSET` | 字元集 | `ISO_IR 192` |

### 功能旗標

| 變數 | 說明 | 預設 |
|------|------|------|
| `FLAG_INCLUDE_PATIENT_INFO_EXCEPT_ID` | DICOM 寫入患者資訊（ID 除外） | `true` |
| `FLAG_INCLUDE_EXAM_DESCRIPTION` | DICOM 寫入檢查記述 | `true` |
| `FLAG_THEME_DARK` | 預設深色主題 | `true` |

### Cloudflare Tunnel

| 變數 | 說明 |
|------|------|
| `CLOUDFLARE_TUNNEL_TOKEN` | 從 Zero Trust 面板取得的 Tunnel Token |

Tunnel 的 Public Hostname Service 填 `http://photo_pacs:9470`。

---

## API 文件

| 方法 | 路徑 | 說明 |
|------|------|------|
| `POST` | `/api/studies` | 上傳影像並送至 PACS |
| `POST` | `/api/pacs/echo` | C-ECHO / DICOMweb 連線測試 |
| `GET` | `/api/settings` | 讀取運行時設定 |
| `PUT` | `/api/settings` | 更新運行時設定 |
| `GET` | `/api/settings/info` | 查詢目前 PACS 後端模式 |
| `GET` | `/healthz` | 健康檢查 |
| `GET` | `/metrics` | 基本指標 |

### POST /api/studies

上傳影像並轉為 DICOM 送至 PACS。使用 `multipart/form-data` 格式。

**參數**：

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `patientId` | string | 是 | 患者 ID |
| `images[]` | file | 是 | 影像檔案（支援多張） |
| `patientName` | string | 否 | 患者姓名 |
| `birthDate` | string | 否 | 出生日期（`YYYY-MM-DD`） |
| `sex` | string | 否 | 性別（`M` / `F` / `O` / `U`） |
| `examDateTime` | string | 否 | 檢查日期時間（ISO 8601），空白則使用目前時間 |
| `examDescription` | string | 否 | 檢查記述 |

**curl 範例**：

```bash
# 上傳兩張影像
curl -X POST http://localhost:9470/api/studies \
  -F "patientId=P-001" \
  -F "patientName=Wang Da Ming" \
  -F "birthDate=1990-01-15" \
  -F "sex=M" \
  -F "examDescription=Skin photo" \
  -F "images[]=@photo1.jpg" \
  -F "images[]=@photo2.jpg"

# 最簡上傳（僅必填欄位）
curl -X POST http://localhost:9470/api/studies \
  -F "patientId=P-001" \
  -F "images[]=@photo.jpg"
```

**成功回應**（200）：

```json
{
  "status": "success",
  "studyInstanceUID": "1.2.826.0.1.3680043...",
  "seriesInstanceUID": "1.2.826.0.1.3680043...",
  "instances": [
    { "index": 1, "sopInstanceUID": "1.2.826.0.1.3680043...", "status": "success" },
    { "index": 2, "sopInstanceUID": "1.2.826.0.1.3680043...", "status": "success" }
  ],
  "pacs": {
    "calledAET": "PACS",
    "host": "192.168.1.100",
    "port": 104
  }
}
```

### POST /api/pacs/echo

測試 PACS 連線。

```bash
curl -X POST http://localhost:9470/api/pacs/echo \
  -H "Content-Type: application/json" \
  -d '{"calledAET":"PACS","host":"192.168.1.100","port":104,"callingAET":"PHOTO_PACS"}'
```

### GET /api/settings

讀取目前的運行時設定。

### PUT /api/settings

更新運行時設定。接受 JSON body，格式與 GET 回傳的 `settings` 欄位相同。

### GET /api/settings/info

回傳目前 PACS 後端模式：

```json
{ "pacsBackend": "cstore" }
```

### GET /healthz

健康檢查。回傳 `{"status": "ok"}`。

### GET /metrics

基本計數指標（請求數、錯誤數等）。

---

## 本機開發

不想用 Docker 的話，可以直接用 Python 開發：

```bash
# 建立虛擬環境
python -m venv .venv

# 啟用
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS / Linux

# 安裝（含開發依賴）
pip install -e .[dev]

# 複製設定檔
cp .env.example .env

# 啟動開發伺服器（預設 mock 模式）
uvicorn photo_pacs.main:app --reload --host 0.0.0.0 --port 9470
```

瀏覽器開啟 `http://localhost:9470`。

Mock 模式不需要真實 PACS，所有送信會模擬成功。

---

## 專案結構

```
photo_pacs/
├── src/photo_pacs/
│   ├── main.py              # FastAPI app 入口
│   ├── settings.py          # 環境變數設定（Pydantic BaseSettings）
│   ├── logging.py           # JSON 格式日誌
│   ├── metrics.py           # 請求計數指標
│   ├── middleware.py         # Request ID、指標 middleware
│   ├── api/
│   │   ├── schemas.py       # Pydantic 回應模型
│   │   └── routes/
│   │       ├── studies.py   # 上傳端點
│   │       ├── pacs.py      # C-ECHO / DICOMweb 測試
│   │       └── settings.py  # 設定 API
│   ├── services/
│   │   ├── conversion.py    # 影像 → DICOM 轉換（PIL + pydicom）
│   │   └── settings_store.py # JSON 持久化運行時設定
│   ├── pacs/
│   │   ├── base.py          # PACS 送信端介面（Protocol）
│   │   ├── mock.py          # Mock 實作（開發測試用）
│   │   ├── cstore.py        # C-STORE 實作（pynetdicom）
│   │   └── dicomweb.py      # DICOMweb STOW-RS 實作（httpx）
│   └── storage/
│       └── local.py         # 本機檔案儲存（上傳/DICOM/清除）
├── web/                     # PWA 前端（靜態 HTML/JS/CSS）
│   ├── index.html           # 主頁面（首頁 + 設定）
│   ├── app.js               # 前端邏輯
│   ├── styles.css           # 樣式
│   ├── sw.js                # Service Worker（離線快取）
│   ├── manifest.json        # PWA manifest
│   └── icons/               # App 圖示
├── tests/                   # pytest 測試（19 個測試案例）
├── docs/                    # 進階文件
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── pyproject.toml
```

---

## 測試

```bash
pytest                          # 全部測試
pytest tests/test_studies.py    # 單一檔案
pytest -v                       # 詳細輸出
```

測試使用 mock PACS 後端，不需要真實 PACS 伺服器。

---

## 錯誤代碼

| HTTP | 代碼 | 說明 |
|------|------|------|
| 400 | `VALIDATION_ERROR` | 表單驗證失敗（缺少必填欄位、格式錯誤、無效影像） |
| 502 | `PACS_REJECTED` | PACS 拒絕傳輸（C-STORE association 失敗或 STOW-RS 錯誤） |
| 504 | `PACS_TIMEOUT` | PACS 連線逾時 |

---

## 常見問題

**Q: 沒有 PACS 伺服器，可以先測試嗎？**

可以。預設 `PACS_BACKEND=mock`，所有送信會模擬成功。

**Q: 上傳後影像存在哪裡？**

暫存在 `data/uploads/`（原始影像）和 `data/dicom/`（DICOM 檔案）。送信成功後預設自動刪除。設定 `KEEP_FILES_ON_SUCCESS=true` 可保留。

**Q: 支援哪些影像格式？**

JPEG、PNG、BMP、WebP、TIFF 等（所有 Pillow 支援的格式）。影像會自動 resize 到長邊上限（預設 1024px）並轉為 RGB。

**Q: 多張影像上傳的 DICOM 結構？**

同一次送出的影像共用相同的 Study / Series Instance UID，每張有獨立的 SOP Instance UID。

**Q: C-STORE 和 DICOMweb 怎麼選？**

- **C-STORE**：傳統 DICOM，TCP 直連。適合區網 PACS。
- **DICOMweb**：HTTPS REST API（STOW-RS）。適合雲端 PACS 或需穿越防火牆。支援 Basic Auth 和 Bearer Token。

**Q: 設定頁改了需要重啟嗎？**

不用。設定會立即寫入 `data/settings.json`，下次送信生效。但 `PACS_BACKEND` 模式只能改 `.env`，需重啟。
