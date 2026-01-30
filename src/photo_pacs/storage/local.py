from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable

from fastapi import UploadFile
from pydicom.dataset import Dataset
from pydicom.filewriter import dcmwrite


class LocalFileStore:
    def __init__(self, upload_dir: Path, dicom_dir: Path) -> None:
        self.upload_dir = upload_dir
        self.dicom_dir = dicom_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.dicom_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(self, upload_id: str, upload_file: UploadFile, index: int) -> Path:
        suffix = Path(upload_file.filename or "").suffix or ".bin"
        dest = self.upload_dir / f"{upload_id}_{index}{suffix.lower()}"
        with dest.open("wb") as handle:
            shutil.copyfileobj(upload_file.file, handle)
        return dest

    def save_dicom(self, upload_id: str, dataset: Dataset) -> Path:
        dest = self.dicom_dir / f"{upload_id}.dcm"
        dcmwrite(str(dest), dataset, write_like_original=False)
        return dest

    def cleanup(self, paths: Iterable[Path]) -> None:
        for path in paths:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                continue
