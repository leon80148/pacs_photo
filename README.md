# Photo PACS

手機/平板拍照上傳，自動轉成 DICOM Secondary Capture 並送入 PACS。

支援 C-STORE（傳統 DICOM）與 DICOMweb（STOW-RS）兩種模式，可透過環境變數切換。內建 Cloudflare Tunnel 支援，外網也能安全使用。

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
    ├─ C-STORE ──▶ PACS 伺服器（傳統 DICOM）
    │
    └─ DICOMweb ─▶ PACS 伺服器（STOW-RS）
```

## 快速開始

### 方式一：Docker Compose（建議）

1. 複製設定檔

```bash
cp .env.example .env
```

2. 編輯 `.env`，至少修改：

```env
PHOTO_PACS_PACS_BACKEND=cstore        # 或 dicomweb
PHOTO_PACS_PACS_HOST=192.168.x.x      # PACS 伺服器 IP
CLOUDFLARE_TUNNEL_TOKEN=eyJhI...       # 若需外網存取
```

3. 啟動

```bash
docker compose up -d --build
```

4. 開啟
   - 區網：`http://<主機IP>:9470`
   - 外網：你在 Cloudflare Tunnel 設定的域名

### 方式二：本機開發

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS / Linux

pip install -e .[dev]
uvicorn photo_pacs.main:app --reload --host 0.0.0.0 --port 9470
```

瀏覽器開啟 `http://localhost:9470`

## PWA 安裝到手機桌面

透過 Cloudflare Tunnel（HTTPS）存取時，瀏覽器會自動提示安裝。

手動安裝：
- **iPhone**：Safari → 分享按鈕 → 加入主畫面
- **Android**：Chrome → 選單（⋮）→ 加到主畫面

## 環境變數

所有變數加上前綴 `PHOTO_PACS_`，完整清單見 `.env.example`。

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

## API

| 方法 | 路徑 | 說明 |
|------|------|------|
| `POST` | `/api/studies` | 上傳影像並送至 PACS（`patientId` 必填） |
| `POST` | `/api/pacs/echo` | C-ECHO / DICOMweb 連線測試 |
| `GET` | `/api/settings` | 讀取運行時設定 |
| `PUT` | `/api/settings` | 更新運行時設定 |
| `GET` | `/api/settings/info` | 查詢目前 PACS 後端模式 |
| `GET` | `/healthz` | 健康檢查 |
| `GET` | `/metrics` | 基本指標 |

### 上傳範例

```bash
curl -X POST http://localhost:9470/api/studies \
  -F "patientId=P-001" \
  -F "images[]=@photo1.jpg" \
  -F "images[]=@photo2.jpg"
```

### POST /api/studies 參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `patientId` | string | 是 | 患者 ID |
| `images[]` | file | 是 | 影像檔案（支援多張） |
| `patientName` | string | 否 | 患者姓名 |
| `birthDate` | string | 否 | 出生日期（`YYYY-MM-DD`） |
| `sex` | string | 否 | 性別（`M` / `F` / `O` / `U`） |
| `examDateTime` | string | 否 | 檢查日期時間（ISO 8601），空白則使用目前時間 |
| `examDescription` | string | 否 | 檢查記述 |

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
│   │   ├── conversion.py    # 影像 → DICOM 轉換
│   │   └── settings_store.py # JSON 持久化運行時設定
│   ├── pacs/
│   │   ├── base.py          # PACS 送信端介面（Protocol）
│   │   ├── mock.py          # Mock 實作
│   │   ├── cstore.py        # C-STORE 實作（pynetdicom）
│   │   └── dicomweb.py      # DICOMweb STOW-RS 實作（httpx）
│   └── storage/
│       └── local.py         # 本機檔案儲存（上傳/DICOM/清除）
├── web/                     # PWA 前端（靜態 HTML/JS/CSS）
├── tests/                   # pytest 測試
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── pyproject.toml
```

## 測試

```bash
pytest                          # 全部測試
pytest tests/test_studies.py    # 單一檔案
pytest -v                       # 詳細輸出
```

## 錯誤代碼

| HTTP | 代碼 | 說明 |
|------|------|------|
| 400 | `VALIDATION_ERROR` | 表單驗證失敗（缺少必填欄位、格式錯誤、無效影像） |
| 502 | `PACS_REJECTED` | PACS 拒絕傳輸 |
| 504 | `PACS_TIMEOUT` | PACS 連線逾時 |

## License

MIT
