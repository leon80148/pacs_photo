# Photo PACS

手機拍照，自動送入 PACS。

用手機或平板拍照、從相簿選圖，自動轉成 DICOM 並送進你的 PACS 伺服器。不需要額外安裝 App，瀏覽器打開就能用。

> **安全聲明**：本工具沒有內建登入機制，請只在信任的網路內使用，或搭配 Cloudflare Access 等認證保護。

## 安裝（Docker）

需要先安裝 [Docker Desktop](https://www.docker.com/products/docker-desktop/) 或 Docker Engine。

**第 1 步：下載專案**

```bash
git clone https://github.com/leon80148/pacs_photo.git
cd pacs_photo
```

**第 2 步：建立設定檔**

```bash
cp .env.example .env
```

**第 3 步：編輯 `.env`**

用文字編輯器打開 `.env`，依照你的 PACS 類型修改（其他不用動）：

**C-STORE（傳統 DICOM，適合區網 PACS）：**

```env
PHOTO_PACS_PACS_BACKEND=cstore
PHOTO_PACS_PACS_HOST=192.168.x.x           # 改成你的 PACS 伺服器 IP
PHOTO_PACS_PACS_PORT=104                    # PACS 的 port（通常是 104）
PHOTO_PACS_PACS_CALLED_AET=PACS            # PACS 的 AE Title
```

**DICOMweb（STOW-RS over HTTPS，適合雲端 PACS）：**

```env
PHOTO_PACS_PACS_BACKEND=dicomweb
PHOTO_PACS_DICOMWEB_BASE_URL=https://host/dcm4chee-arc/aets/DCM4CHEE/rs
```

> 不確定這些值？問你的 PACS 管理員。如果只是想先試用，不用改任何東西，預設的 mock 模式會模擬送信成功。

**第 4 步：啟動**

```bash
docker compose up -d --build
```

**第 5 步：開啟瀏覽器**

在同一個網路的裝置上，打開 `http://<這台電腦的IP>:9470`

例如這台電腦 IP 是 `192.168.1.50`，就在手機瀏覽器輸入 `http://192.168.1.50:9470`

## 設定外網存取（Cloudflare Tunnel）

想在外面也能用（例如帶自己的手機到醫院外上傳）？用 Cloudflare Tunnel 就不用開防火牆 port。

**前置條件**：你需要一個 Cloudflare 帳號，並且有一個域名託管在 Cloudflare。

**第 1 步：建立 Tunnel**

1. 登入 [Cloudflare Zero Trust](https://one.dash.cloudflare.com/)
2. 左側選 **Networks** → **Tunnels**
3. 點 **Create a tunnel**
4. 取個名字（例如 `pacs`），點 Save
5. 在下一頁會看到一串 **Tunnel Token**，複製它

**第 2 步：設定 Token**

打開 `.env`，把 Token 填進去：

```env
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiNjk...（貼上你複製的 Token）
```

**第 3 步：設定對外網址**

回到 Cloudflare Tunnel 設定頁，新增一個 **Public Hostname**：

| 欄位 | 填什麼 |
|------|--------|
| Subdomain | 自己取，例如 `pacs` |
| Domain | 選你在 Cloudflare 的域名 |
| Service Type | HTTP |
| URL | `photo_pacs:9470` |

**第 4 步：重新啟動**

```bash
docker compose up -d --build
```

完成後，用 `https://pacs.你的域名.com` 就能從任何地方存取。

## 安裝到手機桌面（PWA）

透過 HTTPS（Cloudflare Tunnel）存取時，可以把它安裝成像 App 一樣的桌面捷徑：

**iPhone / iPad**：
1. 用 **Safari** 打開網址
2. 點底部的「**分享**」按鈕（方框+箭頭的圖示）
3. 往下滑，選「**加入主畫面**」
4. 點右上角「新增」

**Android**：
1. 用 **Chrome** 打開網址
2. 點右上角的「**⋮**」選單
3. 選「**加到主畫面**」
4. 點「新增」

安裝後從桌面打開，會以全螢幕模式運行，跟一般 App 一樣。

> 區網用 HTTP 可以正常操作，但 PWA 安裝功能需要 HTTPS。

## 如何使用

### 上傳影像

1. 填寫「**患者 ID**」（必填，例如 `A123456`）
2. 其他患者資訊可填可不填（姓名、生日、性別）
3. 點「**拍攝**」開相機拍照，或點「**從相簿選擇**」，可多選
4. 確認照片沒問題後，按「**PACS 送信**」
5. 顯示「送出成功」就完成了

### 設定 PACS 連線

切換到「**設定**」分頁，依照你使用的模式調整連線參數：

- **C-STORE 模式**：修改 PACS 伺服器的 IP、Port、AE Title，用「**測試 C-ECHO**」確認連線
- **DICOMweb 模式**：修改 Base URL、TLS 驗證、逾時秒數，用「**測試連線**」確認連線

改完後按「**儲存設定**」即可，不需要重啟。

## 更多資訊

詳細的環境變數、API 文件、專案結構、開發指南請參考 [進階文件](docs/guide.md)。

## License

MIT
