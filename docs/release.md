# 發佈流程（給維護者）

## 版本更新
1. 更新 `pyproject.toml` 的 `version`
2. 更新 `src/photo_pacs/main.py` 的 `version`

## 打包
1. 執行：`powershell -NoProfile -ExecutionPolicy Bypass -File scripts\package_windows.ps1`
2. 產物在 `release\PhotoPacs-win64.zip`（或帶時間戳）

## 驗證（建議）
1. 解壓 zip
2. 執行 `PhotoPacs.exe`
3. 開 `http://localhost:9470`

## Git 與 Release
1. `git add -A`
2. `git commit -m "release: vX.Y.Z"`
3. `git tag vX.Y.Z`
4. `git push`
5. `git push --tags`
6. 在 GitHub 建立 Release，附件上傳 `PhotoPacs-win64.zip`
