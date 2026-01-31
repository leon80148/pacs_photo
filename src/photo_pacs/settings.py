from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PHOTO_PACS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "photo_pacs"
    environment: str = "dev"
    request_id_header: str = "X-Request-ID"

    upload_dir: Path = Path("data/uploads")
    dicom_dir: Path = Path("data/dicom")
    settings_path: Path = Path("data/settings.json")
    keep_files_on_success: bool = False

    pacs_backend: Literal["mock", "cstore", "dicomweb"] = "mock"
    pacs_host: str = "127.0.0.1"
    pacs_port: int = 104
    pacs_called_aet: str = "PACS"
    local_calling_aet: str = "PHOTO_PACS"

    pacs_tls: bool = False
    pacs_tls_ca_file: Path | None = None
    pacs_tls_cert_file: Path | None = None
    pacs_tls_key_file: Path | None = None

    dicomweb_base_url: str | None = None
    dicomweb_verify_tls: bool = True
    dicomweb_timeout_s: int = Field(default=30, ge=5, le=300)
    dicomweb_auth_method: Literal["none", "basic", "bearer"] = "none"
    dicomweb_username: str | None = None
    dicomweb_password: str | None = None
    dicomweb_token: str | None = None

    local_modality: str = "OT"
    local_resize_max: int = Field(default=1024, ge=256, le=4096)
    local_transfer_syntax: str = "1.2.840.10008.1.2"
    local_charset: str = "ISO_IR 192"

    flag_include_patient_info_except_id: bool = True
    flag_include_exam_description: bool = True
    flag_theme_dark: bool = True

    max_upload_mb: int = Field(default=20, ge=1, le=200)


@lru_cache
def get_settings() -> Settings:
    return Settings()
