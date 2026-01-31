# Photo PACS

手機/平板拍照上傳，自動轉成 DICOM Secondary Capture 並送入 PACS。

支援 C-STORE（傳統 DICOM）與 DICOMweb（STOW-RS）兩種模式，可透過環境變數切換。內建 Cloudflare Tunnel 支援，外網也能安全使用。

> **Security Notice / 安全聲明**
>
> 本 Gateway **不含內建的身份認證機制**。所有 API 端點（包括上傳影像、修改設定）皆無需登入即可存取。
>
> **部署前務必確保**：
> - 僅在受信任的內部網路中使用，或
> - 透過反向代理（如 Cloudflare Access、nginx basic auth）提供認證保護
>
> 未經認證保護的部署可能導致：未授權的影像上傳、PACS 連線設定被竄改、內部網路資訊洩漏。

## 功能特色

- 手機/平板 PWA 拍照或從相簿選擇，支援多張上傳
- 自動將 JPEG/PNG 影像轉換為 DICOM Secondary Capture
- 支援 C-STORE（傳統 DICOM）與 DICOMweb STOW-RS 兩種送信模式
- 內建 C-ECHO / DICOMweb 連線測試
- 運行時設定頁面，即時修改 PACS 連線參數
- Cloudflare Tunnel 整合，免設定 VPN 即可外網存取
- 深色/淺色主題切換
- PHI 敏感資料不寫入日誌

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

## 系統需求

- **Docker 部署**：Docker Engine 20+ 與 Docker Compose V2
- **本機開發**：Python 3.11+
- **PACS 伺服器**：支援 C-STORE（如 dcm4chee、Orthanc）或 DICOMweb STOW-RS

## 快速開始

### 方式一：Docker Compose（建議）

**1. 複製設定檔**

```bash
cp .env.example .env
```

**2. 編輯 `.env`**

根據你的 PACS 模式選擇對應設定：

C-STORE 模式（傳統 DICOM）：

```env
PHOTO_PACS_PACS_BACKEND=cstore
PHOTO_PACS_PACS_HOST=192.168.x.x      # 你的 PACS 伺服器 IP
PHOTO_PACS_PACS_PORT=104               # PACS DICOM port
PHOTO_PACS_PACS_CALLED_AET=PACS        # PACS 的 AE Title
```

DICOMweb 模式（STOW-RS）：

```env
PHOTO_PACS_PACS_BACKEND=dicomweb
PHOTO_PACS_DICOMWEB_BASE_URL=https://pacs.example.com/dcm4chee-arc/aets/DCM4CHEE/rs
```

**3. 啟動**

```bash
docker compose up -d --build
```

**4. 開啟瀏覽器**

- 區網：`http://<主機IP>:9470`
- 外網：你在 Cloudflare Tunnel 設定的域名

### 方式二：本機開發

```bash
# 建立虛擬環境
python -m venv .venv

# 啟用虛擬環境
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS / Linux

# 安裝（含開發依賴）
pip install -e .[dev]

# 複製設定檔
cp .env.example .env
# 編輯 .env 設定 PACS 連線（預設為 mock 模式，不需真實 PACS）

# 啟動開發伺服器
uvicorn photo_pacs.main:app --reload --host 0.0.0.0 --port 9470
```

瀏覽器開啟 `http://localhost:9470`

> **Mock 模式**：預設 `PACS_BACKEND=mock`，不需要真實 PACS 即可測試上傳流程。所有送信都會回傳成功，適合開發與 UI 測試。

## 使用教學

### 首頁：上傳影像

開啟網頁後會看到「首頁」頁面，分為三個區塊：

#### 1. 填寫患者資訊

| 欄位 | 說明 | 是否必填 |
|------|------|----------|
| 患者ID（Patient ID） | 例如 `A123456`，會寫入 DICOM Patient ID 標籤 | **必填** |
| 患者姓名 | 會寫入 DICOM Patient Name 標籤 | 選填 |
| 出生年月日 | 格式 `YYYY-MM-DD`，日期選擇器 | 選填 |
| 性別 | 男 / 女 / 其他 / 未知 | 選填 |

> 患者 ID 為唯一必填欄位。其他欄位空白時，DICOM 檔案對應標籤會留空。

#### 2. 填寫檢查資訊

| 欄位 | 說明 |
|------|------|
| 模式 | **自動**（預設）＝送出時使用當下時間；**手動**＝可自行輸入日期時間 |
| 檢查日期時間 | 自動模式下鎖定，手動模式可選擇 |
| 檢查記述 | 自由文字，會寫入 DICOM Study Description |

#### 3. 選擇影像

- 點擊「**拍攝**」按鈕：開啟相機拍照（手機/平板適用）
- 點擊「**從相簿選擇**」按鈕：從相簿選取，支援多選
- 每張已選的影像會顯示縮圖預覽，可個別刪除
- 支援 JPEG、PNG 等常見格式

#### 4. 送出

確認患者 ID 已填寫、至少選擇一張影像後，「**PACS 送信**」按鈕會變為可點擊。

點擊後：
1. 影像上傳至 Gateway
2. Gateway 自動將每張影像轉成 DICOM Secondary Capture
3. 同一批影像共用相同的 Study Instance UID 和 Series Instance UID
4. 透過 C-STORE 或 DICOMweb 送入 PACS
5. 顯示「送出成功」後，表單自動清空

**送出失敗時的錯誤訊息**：

| 訊息 | 原因 |
|------|------|
| 欄位未填完整或格式錯誤 | 患者 ID 未填、影像格式無效、出生日期格式不對 |
| PACS 連線逾時 | Gateway 無法連上 PACS 伺服器 |
| PACS 拒絕連線或傳輸失敗 | PACS 拒絕 C-STORE association 或 STOW-RS 回傳錯誤 |

### 設定頁

切換到「設定」分頁可即時修改連線參數，**不需重啟服務**。

#### PACS 連線（C-STORE 模式時顯示）

| 欄位 | 說明 | 範例 |
|------|------|------|
| 送信先 AET | PACS 的 AE Title | `PACS`、`DCM4CHEE` |
| 送信先 IP | PACS 伺服器 IP 或 hostname | `192.168.1.100` |
| 送信先 Port | PACS DICOM port | `104`、`11112` |

點擊「**測試 C-ECHO**」可驗證連線是否正常，會顯示成功或失敗訊息。

#### DICOMweb 連線（DICOMweb 模式時顯示）

| 欄位 | 說明 | 範例 |
|------|------|------|
| Base URL | STOW-RS endpoint | `https://pacs.example.com/dcm4chee-arc/aets/DCM4CHEE/rs` |
| 驗證 TLS 證書 | 是否驗證 HTTPS 證書（自簽憑證時可關閉） | 勾選 |
| 逾時秒數 | 請求逾時時間 | `30` |

點擊「**測試連線**」可驗證 DICOMweb endpoint 是否可達。

> 設定頁會根據目前的 `PACS_BACKEND` 環境變數，自動只顯示對應的連線卡片。

#### 進階設定（摺疊區塊）

展開「進階設定」可調整：

**本機送信端**：

| 欄位 | 說明 | 預設 |
|------|------|------|
| 送信元 AET | 本機的 AE Title | `PHOTO_PACS` |
| Modality | DICOM Modality 代碼 | `OT`（Other） |
| 影像長邊尺寸 | 影像 resize 的長邊最大像素 | `1024` |
| Transfer Syntax | DICOM Transfer Syntax UID | `1.2.840.10008.1.2` |
| 字元集 | DICOM Specific Character Set | `ISO_IR 192`（UTF-8） |

**DICOM 寫入旗標**：

| 欄位 | 說明 | 預設 |
|------|------|------|
| 寫入患者資訊（ID 除外） | 將姓名、出生日期、性別寫入 DICOM | 開啟 |
| 寫入檢查記述 | 將 Study Description 寫入 DICOM | 開啟 |

#### 外觀

- **深色主題**：預設開啟，可切換為淺色

修改後點擊「**儲存設定**」。設定會保存到 `data/settings.json`，立即生效。

## PWA 安裝到手機桌面

透過 HTTPS（如 Cloudflare Tunnel）存取時，瀏覽器會自動提示安裝為桌面 App。

手動安裝方式：

- **iPhone / iPad**：Safari 開啟 → 點底部「分享」按鈕 → 「加入主畫面」
- **Android**：Chrome 開啟 → 點右上角選單（⋮）→ 「加到主畫面」

安裝後會以全螢幕 standalone 模式運行，操作體驗接近原生 App。

> PWA 需要 HTTPS 才能安裝。區網使用 HTTP 時可正常操作，但無法安裝到桌面。

## Cloudflare Tunnel 設定

Cloudflare Tunnel 讓外網裝置（如個人手機）能安全存取內網的 Gateway，不需要開放防火牆 port 或設定 VPN。

**設定步驟**：

1. 登入 [Cloudflare Zero Trust](https://one.dash.cloudflare.com/) 控制台
2. 進入 Networks → Tunnels → 建立新 Tunnel
3. 複製 Tunnel Token
4. 在 `.env` 中填入：
   ```env
   CLOUDFLARE_TUNNEL_TOKEN=<你的 Tunnel Token>
   ```
5. 在 Tunnel 設定中新增 Public Hostname：
   - **Subdomain**：自訂（如 `pacs`）
   - **Domain**：你在 Cloudflare 的域名
   - **Service**：`http://photo_pacs:9470`
6. 啟動 Docker Compose：
   ```bash
   docker compose up -d --build
   ```

啟動後，`cloudflared` 容器會在 Gateway 健康檢查通過後才啟動，確保 Tunnel 不會導向未就緒的服務。

> 若不需要外網存取，可將 `CLOUDFLARE_TUNNEL_TOKEN` 留空，`cloudflared` 容器會因缺少 Token 而不啟動，不影響 Gateway 本身運作。

## 環境變數

所有變數加上前綴 `PHOTO_PACS_`（Cloudflare Tunnel Token 除外）。完整清單見 `.env.example`。

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

測試 PACS 連線。C-STORE 模式發送 C-ECHO，DICOMweb 模式發送 HTTP 請求。

```bash
curl -X POST http://localhost:9470/api/pacs/echo \
  -H "Content-Type: application/json" \
  -d '{"calledAET":"PACS","host":"192.168.1.100","port":104,"callingAET":"PHOTO_PACS"}'
```

### GET /api/settings

讀取目前的運行時設定（PACS 連線、DICOM 參數、功能旗標）。

### PUT /api/settings

更新運行時設定。接受 JSON body，格式與 GET 回傳的 `settings` 欄位相同。

### GET /api/settings/info

回傳目前使用的 PACS 後端模式：

```json
{ "pacsBackend": "cstore" }
```

### GET /healthz

健康檢查端點。回傳 `{"status": "ok"}`。

### GET /metrics

回傳基本計數指標（請求數、錯誤數等）。

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

測試使用 mock PACS 後端，不需要真實 PACS 伺服器。

## 錯誤代碼

| HTTP | 代碼 | 說明 |
|------|------|------|
| 400 | `VALIDATION_ERROR` | 表單驗證失敗（缺少必填欄位、格式錯誤、無效影像） |
| 502 | `PACS_REJECTED` | PACS 拒絕傳輸（C-STORE association 失敗或 STOW-RS 回傳錯誤） |
| 504 | `PACS_TIMEOUT` | PACS 連線逾時 |

## 常見問題

**Q: 沒有 PACS 伺服器，可以先測試嗎？**

可以。預設 `PACS_BACKEND=mock`，所有送信操作會模擬成功。適合 UI 開發和流程驗證。

**Q: 上傳後影像存在哪裡？**

暫存在 `data/uploads/`（原始影像）和 `data/dicom/`（DICOM 檔案）。送信成功後預設會自動刪除。設定 `KEEP_FILES_ON_SUCCESS=true` 可保留。

**Q: 支援哪些影像格式？**

所有 Pillow 支援的格式，包括 JPEG、PNG、BMP、WebP、TIFF 等。影像會自動 resize 到設定的長邊上限（預設 1024px）並轉為 RGB 模式。

**Q: 多張影像上傳的 DICOM 結構是什麼？**

同一次送出的所有影像共用相同的 Study Instance UID 和 Series Instance UID，每張影像有獨立的 SOP Instance UID。

**Q: C-STORE 和 DICOMweb 怎麼選？**

- **C-STORE**：傳統 DICOM 協定，直接透過 TCP 連線送信。適合區網內的 PACS。
- **DICOMweb**：透過 HTTPS REST API（STOW-RS）送信。適合雲端 PACS 或需要穿越防火牆的場景。支援 Basic Auth 和 Bearer Token 認證。

透過 `.env` 的 `PACS_BACKEND` 切換，程式碼無需修改。

**Q: 設定頁修改後需要重啟嗎？**

不需要。設定頁的修改會立即寫入 `data/settings.json`，下次送信時生效。但 `PACS_BACKEND` 模式只能透過環境變數（`.env`）修改，需重啟服務。

## License

MIT
