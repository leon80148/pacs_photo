以下是根據你目前提供的介面與需求，整理出的 **《PACS 拍照上傳 PWA + Gateway 技術規格書（SPEC）》**（繁體中文、可直接交付工程師開工）。

---

# PACS 拍照上傳 PWA + Gateway 技術規格書（SPEC）

## 1. 目標與範圍

### 1.1 產品目標

提供診所使用的 **PWA 應用**，讓人員以手機/平板：

* 拍照或從相簿多選照片
* 由後端 Gateway 將照片封裝為 **DICOM Secondary Capture**
* 透過 **DIMSE（C-STORE）** 上傳至區網內的 **dcm4chee（PACS）**

### 1.2 必要條件（已定案）

* **一次按「PACS 送信」＝建立 1 個新 Study**
* 同一次送出的多張照片 → **同一個 Series**、不同 SOP Instance
* DICOM 類型：**Secondary Capture（相容性優先）**
* 患者資料：**Patient ID 或 病歷號 擇一必填**
* 其餘患者資料（姓名/生日/性別）可填可不填，且可由設定決定是否寫入 DICOM
* 送出成功後：**全部清空**
* HIS/EMR：有 **HTTP API**，以 **API Key** 驗證，用於病患資料補齊
* 規則：**若 Patient ID 與 病歷號都填，且與 HIS 查回結果不一致 → 擋下並要求修正（選項 3）**

### 1.3 未來擴充（預留）

* dcm4chee 開啟 DICOMweb 後，支援 **STOW-RS** 上傳（可由 Gateway 切換策略）

---

## 2. 系統架構總覽

### 2.1 架構（文字描述）

* **使用者裝置（手機/平板）**

  * 瀏覽器/PWA（HTTPS）
  * 相機/相簿取圖
* **診所區網主機（同一台部署）**

  1. 靜態網站服務（PWA 前端）
  2. Gateway API（HTTPS）
  3. DICOM Sender（Gateway 內部模組）：DIMSE C-ECHO / C-STORE
  4. Patient Lookup（Gateway 內部模組）：呼叫 HIS/EMR API
* **dcm4chee（PACS）**

  * DIMSE SCP（接收 C-STORE）
  * 回應狀態（Success / Failure）

### 2.2 資料流

1. PWA 收集表單 + 多張影像 → `POST /api/studies`
2. Gateway 驗證輸入、必要時呼叫 HIS/EMR 補齊 PatientID/資料
3. Gateway 產生 DICOM（SC）→ 以 C-STORE 傳至 dcm4chee
4. 回傳上傳結果（成功、失敗原因、失敗可重送）

---

## 3. 技術棧與環境（建議實作）

> 你沒有指定語言/框架，以下是「最常見且好維護」的一組建議；若你們既有技術偏好可替換，但 SPEC 的介面與流程不變。

### 3.1 前端（PWA）

* Framework：React / Vue / Svelte 皆可（建議 React）
* PWA：Service Worker、App Manifest
* UI：深色主題、卡片式區塊、底部 Tab（首頁/設定）
* 圖片取得：

  * 相機：`<input type="file" accept="image/*" capture="environment">`
  * 相簿多選：`multiple` + `accept="image/*"`
* 本地儲存：IndexedDB（或 LocalStorage 只存設定；影像建議 IndexedDB/Memory）

### 3.2 後端（Gateway）

* API：Node.js (Fastify/Express) 或 Python (FastAPI) 擇一
* DICOM：

  * 建議用現成 DICOM library 產生 SC（例如 Python pydicom / Node 相關 lib）
  * DIMSE Sender：

    * 建議 Gateway 透過 **dcmtk / dcm4che 工具**或程式庫執行 C-ECHO/C-STORE
    * 以子行程/服務封裝，統一管理重試、timeout、log

### 3.3 部署

* Docker Compose（建議）
* 反向代理：Nginx / Caddy（HTTPS、同網域提供 PWA + API）
* 憑證：診所內可用自簽或內部 CA；建議至少 HTTPS（避免瀏覽器限制與安全問題）

---

## 4. 功能模組規格

## 4.1 PWA 介面與互動

### 4.1.1 導覽

* 底部 Tab：

  * `首頁`
  * `設定`

### 4.1.2 首頁（Home）— 欄位區塊

#### A. 患者資訊（卡片）

欄位：

* `患者ID（Patient ID）`：文字輸入
* `病歷號`：文字輸入
* `患者姓名`：文字輸入（可空）
* `出生年月日`：日期選擇（可空）
* `性別`：選單（男/女/其他/未知，可空）

規則：

* **患者ID 與 病歷號 至少填一個**
* 提供「清除」按鈕：清空該卡片欄位

#### B. 檢查資訊（卡片）

欄位：

* `模式`：手動 / 自動
* `檢查日期時間`

  * 自動：預設帶入目前時間，可切換修改
* `檢查記述`：文字輸入（可空）
* 「清除」按鈕：清空該卡片欄位

#### C. 影像資訊（卡片）

功能：

* `拍攝`：開啟相機拍照（可多次）
* `從相簿選擇`：相簿多選（一次可選多張，可再追加）
* 顯示影像縮圖清單：

  * 每張可「刪除」
  * 顯示張數（例如：已選 6 張）
* 「清除」按鈕：清空全部影像

#### D. 送出

* 大按鈕：`PACS 送信`
* 送出前檢核：

  * 至少一張影像
  * （患者ID 或 病歷號）至少一個
  * 其餘欄位視為選填
* 送出中狀態：

  * Loading / 進度（可顯示：已送出 X/N）
* 成功：

  * 顯示成功提示
  * **清空所有欄位（患者/檢查/影像全清）**
* 失敗：

  * 顯示錯誤原因（可讀）
  * 保留資料供重送（建議；可在錯誤提示中提供「重試」）

---

## 4.2 設定頁（Settings）

### 4.2.1 PACS 連線（Archive AE）

* `送信先 AET`
* `送信先 IP`
* `送信先 Port`
* 按鈕：`測試 C-ECHO`

  * 成功顯示：連線成功
  * 失敗顯示：錯誤原因（timeout、拒絕、AET 不符等）

### 4.2.2 本機送信端（Local AE）

* `送信元 AET`（預設：Phone）
* `Modality`（預設：OT）
* `影像長邊尺寸`（預設：1024）
* `Transfer Syntax`（預設：Implicit VR Little Endian）
* `字元集（Specific Character Set）`（預設：可先用 UTF-8 對應常見設定；若需相容日系/舊系統再調）

### 4.2.3 DICOM 寫入開關（隱私）

* 開關：`寫入患者資訊（ID 除外）`

  * OFF：即使前端填了姓名/生日/性別，也 **不寫入 DICOM**
* 開關：`寫入檢查記述`

  * OFF：不寫入（例如不寫入 StudyDescription/SeriesDescription）

### 4.2.4 HIS/EMR 串接設定

* `HIS API Base URL`
* `HIS API Key`
* （可選）`查詢逾時秒數`、`重試次數`

### 4.2.5 外觀

* 開關：`深色主題`（預設 ON）

---

## 5. Patient Lookup（病患主檔補齊）規格

### 5.1 查詢觸發條件

Gateway 在建立 Study 前做 Patient Lookup：

* 若輸入只有 `病歷號`（無 PatientID） → **必查**
* 若同時有 `患者ID` 與 `病歷號` → **必查**，並做一致性檢查（見 5.2）
* 若只有 `患者ID`（無病歷號）：

  * 可做成設定選項（預設：不查，以減少依賴）
  * 本期可先「不查」

### 5.2 一致性規則（你要求的選項 3）

當 `患者ID` 與 `病歷號` 皆提供：

1. Gateway 用病歷號查 HIS → 得到 `hisPatientId`
2. 若 `hisPatientId != 輸入患者ID` → **拒絕送出**

   * 回傳錯誤碼：`PATIENT_ID_MISMATCH`
   * 訊息：`患者ID與病歷號查回資料不一致，請確認後再送出。`

> 目的：避免 PACS 產生錯誤歸戶。

### 5.3 HIS API 需求（抽象定義）

> 你們實際 API 路徑/欄位可能不同，此處定義 Gateway 需要的最小資料結構。

* 請求：以病歷號查病患
* 回應需包含（至少）：

  * `patientId`（對應 DICOM PatientID）
  * 可選：`name`、`birthDate`、`sex`

若查不到：

* 回傳錯誤：`PATIENT_NOT_FOUND`

若查到多筆（理論上不該發生，但要防）：

* 回傳錯誤：`PATIENT_AMBIGUOUS`

---

## 6. DICOM 生成規格（Secondary Capture）

### 6.1 Study / Series / Instance 生成規則

* 每次 `PACS 送信` 建立：

  * `StudyInstanceUID`：新生成
  * `SeriesInstanceUID`：新生成
  * `SOPInstanceUID`：每張影像各自新生成
* 多張照片：

  * 同一個 Series
  * `InstanceNumber` 依使用者清單順序 1..N

### 6.2 影像處理

* Resize：

  * 依設定 `影像長邊尺寸`（預設 1024）
  * 保持比例，短邊自動縮放
* 色彩：

  * 優先保留 RGB（若 lib/流程要求也可轉成常見格式）
* 壓縮：

  * 本期採 **不壓縮/或依 Transfer Syntax**（以相容性為準）
* 方向資訊：

  * 手機 EXIF 方向需校正（避免 PACS 顯示旋轉錯誤）

### 6.3 DICOM Tag 寫入（核心）

> 下列為「建議最小集合」，可確保 PACS 可用並可追溯。

**患者（Patient）**

* (0010,0020) PatientID：必填（由輸入或 HIS 查回）
* (0010,0010) PatientName：可選（受設定開關控制）
* (0010,0030) PatientBirthDate：可選（受設定開關控制）
* (0010,0040) PatientSex：可選（受設定開關控制）

**研究（Study）**

* (0020,000D) StudyInstanceUID：必填
* (0008,0020) StudyDate：由「檢查日期時間」取日期
* (0008,0030) StudyTime：由「檢查日期時間」取時間
* (0008,1030) StudyDescription：可選（若「寫入檢查記述」= ON）

**序列（Series）**

* (0020,000E) SeriesInstanceUID：必填
* (0020,0011) SeriesNumber：固定 1 或自增（本期固定 1）
* (0008,0060) Modality：預設 OT（可設定）
* (0008,103E) SeriesDescription：可選（可放檢查記述或固定值，例如「診所拍照上傳」）

**影像（Instance / Image）**

* (0008,0016) SOPClassUID：Secondary Capture Image Storage
* (0008,0018) SOPInstanceUID：必填
* (0020,0013) InstanceNumber：1..N
* (0008,0064) ConversionType：例如 WSD（依實作）
* Pixel Data 相關（Rows/Columns/SamplesPerPixel/PhotometricInterpretation/BitsAllocated 等由 library 正確填入）

**字元集（Specific Character Set）**

* 由設定提供（預設值由你們現場 PACS 相容性決定；若不確定可先用常見 UTF-8 對應）

---

## 7. Gateway API 規格

### 7.1 認證

* PWA ↔ Gateway：同網段內使用，建議至少：

  * 基礎：不登入（區網限制 + HTTPS）
  * 進階：簡易 PIN / 帳號密碼 / 裝置白名單（可列入後續）
* Gateway ↔ HIS：API Key（header）

### 7.2 Endpoints

#### 7.2.1 建立並上傳 Study

`POST /api/studies`

**Request（multipart/form-data）**

* `patientId` (string, optional)
* `chartNo` 病歷號 (string, optional)
* `patientName` (string, optional)
* `birthDate` (string, optional, YYYY-MM-DD)
* `sex` (string, optional, M/F/O/U)
* `examDateTime` (string, optional, ISO 8601；未提供則 Gateway 用現在)
* `examDescription` (string, optional)
* `images[]` (file, required, 1..N)

**Validation**

* `patientId` 或 `chartNo` 至少一個
* `images[]` 至少一張
* 若 `chartNo` 存在 → 需 HIS 查回 `patientId`
* 若同時提供 `patientId` + `chartNo`：

  * 查回的 `hisPatientId` 必須與 `patientId` 相同，否則 409

**Response 200**

```json
{
  "status": "success",
  "studyInstanceUID": "2.25....",
  "seriesInstanceUID": "2.25....",
  "instances": [
    { "index": 1, "sopInstanceUID": "2.25....", "status": "stored" },
    { "index": 2, "sopInstanceUID": "2.25....", "status": "stored" }
  ],
  "pacs": {
    "calledAET": "DCM4CHEE",
    "host": "192.168.1.10",
    "port": 11112
  }
}
```

**Error Codes**

* 400 `VALIDATION_ERROR`：必填缺漏、檔案格式不符
* 404 `PATIENT_NOT_FOUND`：病歷號查不到
* 409 `PATIENT_ID_MISMATCH`：你選的規則（ID 與病歷號不一致）
* 502 `HIS_UNAVAILABLE`：HIS 連不上/timeout
* 504 `PACS_TIMEOUT`：C-STORE 或 C-ECHO timeout
* 502 `PACS_REJECTED`：PACS 拒絕、Association fail、AET 不符等
* 500 `INTERNAL_ERROR`：未預期錯誤（需記錄 requestId 便於追查）

---

#### 7.2.2 PACS 連線測試

`POST /api/pacs/echo`

**Request**

```json
{
  "calledAET": "DCM4CHEE",
  "host": "192.168.1.10",
  "port": 11112,
  "callingAET": "Phone"
}
```

**Response 200**

```json
{ "status": "success", "message": "C-ECHO OK" }
```

**Response 502/504**

```json
{ "status": "failure", "code": "PACS_TIMEOUT", "message": "C-ECHO timeout" }
```

---

#### 7.2.3 讀取/更新設定

* `GET /api/settings`
* `PUT /api/settings`

設定內容包含：

* PACS：calledAET/host/port
* Local AE：callingAET/modality/resizeMax/transferSyntax/charset
* Flags：includePatientInfoExceptId/includeExamDescription/themeDark
* HIS：baseUrl/apiKey/timeout/retry

---

## 8. 錯誤處理與可維護性

### 8.1 前端顯示原則

* 使用者可理解的訊息（繁中）
* 顯示「可行的下一步」

  * `病歷號查不到` → 請確認病歷號是否正確
  * `患者ID不一致` → 請修正患者ID或病歷號其一
  * `PACS 連線失敗` → 請先到設定頁測試 C-ECHO

### 8.2 Gateway 記錄（Log）

* 每次上傳建立 `requestId`
* 記錄：

  * 查 HIS 結果（遮蔽敏感資料）
  * 產生的 Study/Series UID
  * 每張 instance 的 C-STORE 狀態
  * PACS association 錯誤原因（可讀）

---

## 9. 安全性與限制

### 9.1 限制（重要）

* PWA 不能直接做 DIMSE TCP 連線，所以必須透過 Gateway。

### 9.2 建議安全措施

* Gateway 使用 HTTPS
* HIS API Key 僅存在 Gateway（前端不保存）
* 設定頁可加簡易管理密碼（避免一般人修改 PACS/HIS 設定）— 可列入後續

---

## 10. 測試與驗收準則

### 10.1 功能驗收（核心）

1. **相簿多選 + 拍照追加**：能組成 N 張影像清單、可刪單張、可清空
2. **送出建立新 Study**：同一次送出多張 → PACS 中同一 Study/Series 可看到多張
3. **送出成功清空**：成功後患者/檢查/影像全部清空
4. **病歷號補齊**：只填病歷號可成功上傳，DICOM PatientID 正確
5. **一致性阻擋**：同時填患者ID+病歷號但不一致 → 阻擋（409 PATIENT_ID_MISMATCH）
6. **隱私開關**：

   * 關閉「寫入患者資訊（ID除外）」：DICOM 不含姓名/生日/性別
7. **C-ECHO 測試**：設定頁可測通/測不通並顯示原因

### 10.2 例外測試

* HIS timeout / 回 500 → 顯示 HIS 無法使用
* PACS timeout / 拒絕 association → 顯示 PACS 連線問題
* 上傳途中第 k 張失敗：

  * 回傳 instances 狀態（stored/failed）
  * 前端顯示「部分失敗」與重送建議（本期可先整批視為失敗並保留資料）

---

## 11. 後續可選增強（不影響本期上線）

* 條碼/QR 掃描（掃病歷號或 PatientID）
* 上傳佇列（背景重送、離線暫存）
* 使用者登入/角色（管理者可改設定）
* DICOMweb（STOW-RS）模式切換
* 將「檢查記述」細分為 StudyDescription / SeriesDescription
* 影像壓縮選項（JPEG Baseline）以減少檔案大小（需驗證相容性）

---

如果你願意，我下一步可以直接把「**介面文字（繁中）逐條對照**」也整理成一份 UI 文案清單（包含按鈕、欄位 placeholder、錯誤訊息），讓前端可以照表實作、並保持跟你截圖風格一致。

你只要回覆一句：「要 UI 文案清單」，我就會接著給你。
