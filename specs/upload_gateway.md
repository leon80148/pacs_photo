# 規格：PACS 拍照上傳 PWA + Gateway

## 問題
PACS 目前不支援 DICOMweb，但診所需要用手機/平板拍照或上傳照片並送入 PACS，因此必須建立 PWA 與暫時性 gateway。

## 目標
- 提供 PWA 表單與多圖上傳流程。
- Gateway 將影像封裝為 DICOM Secondary Capture。
- 以 DIMSE C-STORE 傳送至 PACS。
- 提供 C-ECHO 測試與可調整設定。
- 病歷號可透過 HIS 查詢補齊 PatientID，並做一致性檢查。

## 非目標
- DICOMweb（STOW-RS）實作。
- 完整帳號/權限系統（可保留擴充點）。
- 進階影像壓縮或醫療影像校正流程。

## 使用者流程
1. 使用者在 PWA 填入病患與檢查資訊，選擇多張影像。
2. PWA 送出 `POST /api/studies`。
3. Gateway 驗證資料並視需要查 HIS。
4. 產生 DICOM（SC），以 C-STORE 送至 PACS。
5. 回傳結果，PWA 顯示成功或失敗原因。

## API / 契約
### POST `/api/studies`（multipart/form-data）
欄位：
- `patientId`（optional）
- `chartNo`（optional）
- `patientName`（optional）
- `birthDate`（optional, YYYY-MM-DD）
- `sex`（optional, M/F/O/U）
- `examDateTime`（optional, ISO 8601）
- `examDescription`（optional）
- `images[]`（required, 1..N）

驗證：
- `patientId` 或 `chartNo` 至少一個
- `images[]` 至少一張
- 若 `chartNo` 存在 → 必查 HIS 取得 `patientId`
- 若 `patientId` + `chartNo` 同時提供 → HIS 查回的 `patientId` 必須一致，否則 409

成功回應（200）：
```json
{
  "status": "success",
  "studyInstanceUID": "2.25....",
  "seriesInstanceUID": "2.25....",
  "instances": [
    { "index": 1, "sopInstanceUID": "2.25....", "status": "stored" }
  ],
  "pacs": { "calledAET": "PACS", "host": "127.0.0.1", "port": 104 }
}
```

錯誤回應：
- 400 `VALIDATION_ERROR`
- 404 `PATIENT_NOT_FOUND`
- 409 `PATIENT_ID_MISMATCH`
- 502 `HIS_UNAVAILABLE`
- 504 `PACS_TIMEOUT`
- 502 `PACS_REJECTED`
- 500 `INTERNAL_ERROR`

### POST `/api/pacs/echo`
Request：
```json
{ "calledAET": "PACS", "host": "127.0.0.1", "port": 104, "callingAET": "Phone" }
```

Response 200：
```json
{ "status": "success", "message": "C-ECHO OK" }
```

### GET/PUT `/api/settings`
設定內容：
- PACS：calledAET/host/port
- Local AE：callingAET/modality/resizeMax/transferSyntax/charset
- Flags：includePatientInfoExceptId/includeExamDescription/themeDark
- HIS：baseUrl/apiKey/timeout/retry

### GET `/healthz`, GET `/metrics`
基本健康檢查與指標。

## 資料模型
### Settings
- `pacs`: { calledAET, host, port }
- `localAE`: { callingAET, modality, resizeMax, transferSyntax, charset }
- `flags`: { includePatientInfoExceptId, includeExamDescription, themeDark }
- `his`: { baseUrl, apiKey, timeout, retry }

### DICOM（最小標籤）
- Secondary Capture SOP Class
- 同一請求共用 Study/Series UID
- 每張影像獨立 SOPInstanceUID、InstanceNumber
- PatientID 必填；其餘欄位由設定控制
- Modality 預設 OT（可設定）

## 錯誤處理
- HIS 查不到 → 404
- HIS 無法連線/逾時 → 502
- PatientID 不一致 → 409
- PACS association 失敗或拒絕 → 502
- C-STORE timeout → 504

## 安全與隱私
- PHI 不可寫入日誌；必要時遮罩或雜湊。
- 請求需有 requestId 方便稽核。
- HTTPS 與 PACS TLS 可設定。

## 驗收標準
1. 可多選照片並送出，PACS 內同一 Study/Series 看到多張影像。
2. 只填病歷號時能透過 HIS 查回 PatientID 並送出。
3. PatientID 與病歷號不一致會被阻擋（409）。
4. 成功送出後可清空畫面資料。
5. 可進行 C-ECHO 測試並回報結果。
6. 日誌不含 PHI，回應或 header 含 requestId。

## 測試計畫
- API 測試：/api/studies 成功/失敗情境。
- HIS 查詢：命中、查不到、timeout。
- PACS C-STORE：mock 成功/失敗。
- DICOM 檔案檢查：Study/Series/Instance 規則正確。
- /api/pacs/echo、/api/settings、/healthz、/metrics 回應正常。
