from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from photo_pacs.main import create_app
from photo_pacs.settings import Settings, get_settings


@pytest.fixture()
def make_client(tmp_path):
    def _make(overrides: dict | None = None):
        params = {
            "upload_dir": tmp_path / "uploads",
            "dicom_dir": tmp_path / "dicom",
            "settings_path": tmp_path / "settings.json",
            "keep_files_on_success": True,
            "pacs_backend": "mock",
            "his_backend": "mock",
        }
        if overrides:
            params.update(overrides)

        settings = Settings(**params)
        app = create_app()
        app.dependency_overrides[get_settings] = lambda: settings
        app.state.settings = settings
        app.state.request_id_header = settings.request_id_header
        return TestClient(app), settings

    return _make
