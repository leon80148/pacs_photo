from __future__ import annotations

import configparser
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import (
    DEFAULT_PATH,
    ConfigFileSourceMixin,
    InitSettingsSource,
    PydanticBaseSettingsSource,
)


def _dotenv_config_path() -> str | None:
    dotenv_path = Path(".env")
    if not dotenv_path.is_file():
        return None
    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() == "PHOTO_PACS_CONFIG":
            return value.strip().strip("\"'")
    return None


def _default_ini_paths() -> list[Path]:
    env_path = os.getenv("PHOTO_PACS_CONFIG")
    if env_path:
        return [Path(env_path)]
    dotenv_path = _dotenv_config_path()
    if dotenv_path:
        return [Path(dotenv_path)]
    paths: list[Path] = []
    if getattr(sys, "frozen", False):
        paths.append(Path(sys.executable).resolve().parent / "config.ini")
    paths.append(Path.cwd() / "config.ini")
    return paths


def _normalize_ini_key(key: str) -> str:
    normalized = key.strip().lower()
    if normalized.startswith("photo_pacs_"):
        normalized = normalized[len("photo_pacs_") :]
    return normalized


class IniConfigSettingsSource(InitSettingsSource, ConfigFileSourceMixin):
    def __init__(
        self,
        settings_cls: type[BaseSettings],
        ini_file: str | Path | list[str | Path] | None = DEFAULT_PATH,
        ini_file_encoding: str | None = None,
    ) -> None:
        if ini_file == DEFAULT_PATH:
            ini_file = settings_cls.model_config.get("ini_file")
        if ini_file is None:
            ini_file = _default_ini_paths()
        self.ini_file_path = ini_file
        self.ini_file_encoding = (
            ini_file_encoding
            if ini_file_encoding is not None
            else settings_cls.model_config.get("ini_file_encoding")
        )
        self.ini_section = settings_cls.model_config.get("ini_section", "photo_pacs")
        self.ini_data = self._read_files(self.ini_file_path)
        super().__init__(settings_cls, self.ini_data)

    def _read_file(self, file_path: Path) -> dict[str, Any]:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(file_path, encoding=self.ini_file_encoding)
        data: dict[str, Any] = {}
        for key, value in parser.defaults().items():
            data[_normalize_ini_key(key)] = value
        section: str | None = None
        if self.ini_section and parser.has_section(self.ini_section):
            section = self.ini_section
        elif parser.sections():
            section = parser.sections()[0]
        if section:
            for key, value in parser.items(section):
                data[_normalize_ini_key(key)] = value
        return data

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(ini_file={self.ini_file_path})"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PHOTO_PACS_",
        env_file=".env",
        env_file_encoding="utf-8",
        ini_file_encoding="utf-8",
        ini_section="photo_pacs",
        extra="ignore",
    )

    app_name: str = "photo_pacs"
    environment: str = "dev"
    request_id_header: str = "X-Request-ID"
    server_host: str = "0.0.0.0"
    server_port: int = Field(default=9470, ge=1, le=65535)

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

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        ini_settings = IniConfigSettingsSource(settings_cls)
        return (
            init_settings,
            env_settings,
            ini_settings,
            dotenv_settings,
            file_secret_settings,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
