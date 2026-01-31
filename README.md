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

### 必填

| 變數 | 說明 | 預設 |
|------|------|------|
| `PACS_BACKEND` | PACS 後端模式 | `mock` |

### C-STORE 模式

| 變數 | 說明 | 預設 |
|------|------|------|
| `PACS_HOST` | PACS 伺服器 IP | `127.0.0.1` |
| `PACS_PORT` | PACS port | `104` |
| `PACS_CALLED_AET` | 對方 AE Title | `PACS` |
| `LOCAL_CALLING_AET` | 本機 AE Title | `PHOTO_PACS` |

### DICOMweb 模式

| 變數 | 說明 | 預設 |
|------|------|------|
| `DICOMWEB_BASE_URL` | STOW-RS Base URL | （無） |
| `DICOMWEB_VERIFY_TLS` | 驗證 TLS 證書 | `true` |
| `DICOMWEB_TIMEOUT_S` | 逾時秒數 | `30` |
| `DICOMWEB_AUTH_METHOD` | 認證方式 | `none` |

### Cloudflare Tunnel

| 變數 | 說明 |
|------|------|
| `CLOUDFLARE_TUNNEL_TOKEN` | 從 Zero Trust 面板取得的 Tunnel Token |

Tunnel 的 Public Hostname Service 填 `http://photo_pacs:9470`。

## API

| 方法 | 路徑 | 說明 |
|------|------|------|
| `POST` | `/api/studies` | 上傳影像並送至 PACS |
| `POST` | `/api/pacs/echo` | C-ECHO 連線測試 |
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

## 專案結構

```
photo_pacs/
├── src/photo_pacs/
│   ├── main.py              # FastAPI app 入口
│   ├── settings.py          # 環境變數設定
│   ├── middleware.py         # Request ID、指標
│   ├── api/routes/
│   │   ├── studies.py       # 上傳端點
│   │   ├── pacs.py          # C-ECHO 測試
│   │   └── settings.py      # 設定 API
│   ├── services/
│   │   ├── conversion.py    # 影像 → DICOM 轉換
│   │   └── settings_store.py
│   └── pacs/
│       ├── base.py          # PACS 介面
│       ├── cstore.py        # C-STORE 實作
│       └── dicomweb.py      # DICOMweb 實作
├── web/                     # PWA 前端（靜態）
├── tests/
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── pyproject.toml
```

## 測試

```bash
pytest
```

## 錯誤代碼

| HTTP | 代碼 | 說明 |
|------|------|------|
| 400 | `VALIDATION_ERROR` | 表單驗證失敗 |
| 502 | `PACS_REJECTED` | PACS 拒絕傳輸 |
| 504 | `PACS_TIMEOUT` | PACS 連線逾時 |
