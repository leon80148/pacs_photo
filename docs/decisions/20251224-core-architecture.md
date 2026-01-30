# 決策紀錄：核心架構

日期：2025-12-24

## 決策
1. 使用 FastAPI 作為 HTTP gateway。
2. 設定集中於單一 settings 模組，以環境變數提供預設值。
3. 暫存使用本機檔案系統（`data/`），成功送出後清除檔案。
4. PACS 後端以介面抽象，先提供 mock 與 C-STORE，保留 DICOMweb 介面但不實作。
5. 前端先以靜態 HTML/JS 做 PWA，避免前期導入大型框架。
6. 設定讀寫以 JSON 檔案保存（`data/settings.json`），供 `/api/settings` 使用。
7. DICOM 轉換以 Secondary Capture 為主，Transfer Syntax 預設 Implicit VR Little Endian。

## 理由
- 專案需快速落地，且要為未來 DICOMweb 切換保留彈性。
- 靜態 PWA 容易部署與維護，可快速驗證流程。
- JSON 設定便於前端設定頁即時修改。

## 影響
- 若後續改用前端框架或資料庫設定，需要調整部署方式。
- DICOM 標籤較精簡，未涵蓋進階醫療資訊欄位。
