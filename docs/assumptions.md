# 假設（Assumptions）

日期：2025-12-24

1. `photo_pacs_PRD.md` 為 UTF-8 編碼，讀取時需指定 UTF-8 才能正確顯示內容。
2. 後端採 FastAPI 實作，前端 PWA 先以靜態 HTML/JS 實作（非 React/Vue），以縮短交付時間。
3. HIS 查詢 API 以 `GET {base_url}/patients?chartNo=...` 為預設格式；實際路徑可由設定調整。
4. `chartNo` 需要 HIS 查詢才能補齊 PatientID；若 HIS 未設定或不可用，回 `HIS_UNAVAILABLE`。
5. DICOM 影像處理：依 `resizeMax` 等比例縮放長邊，並套用 EXIF 方向修正。
6. 轉換採 Secondary Capture，Transfer Syntax 預設 Implicit VR Little Endian。
7. 開發階段使用本機檔案系統暫存影像與 DICOM，送出成功即清除。
