from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from photo_pacs.settings import Settings


class PacsConfig(BaseModel):
    called_aet: str = Field(alias="calledAET")
    host: str
    port: int

    model_config = {"populate_by_name": True}


class LocalAEConfig(BaseModel):
    calling_aet: str = Field(alias="callingAET")
    modality: str
    resize_max: int = Field(alias="resizeMax")
    transfer_syntax: str = Field(alias="transferSyntax")
    charset: str

    model_config = {"populate_by_name": True}


class FlagsConfig(BaseModel):
    include_patient_info_except_id: bool = Field(alias="includePatientInfoExceptId")
    include_exam_description: bool = Field(alias="includeExamDescription")
    theme_dark: bool = Field(alias="themeDark")

    model_config = {"populate_by_name": True}


class DicomwebConfig(BaseModel):
    base_url: str | None = Field(default=None, alias="baseUrl")
    verify_tls: bool = Field(default=True, alias="verifyTls")
    timeout: int = 30

    model_config = {"populate_by_name": True}


class RuntimeSettings(BaseModel):
    pacs: PacsConfig
    dicomweb: DicomwebConfig = Field(default_factory=DicomwebConfig)
    local_ae: LocalAEConfig = Field(alias="localAE")
    flags: FlagsConfig

    model_config = {"populate_by_name": True}


def build_default_runtime_settings(settings: Settings) -> RuntimeSettings:
    return RuntimeSettings(
        pacs=PacsConfig(
            called_aet=settings.pacs_called_aet,
            host=settings.pacs_host,
            port=settings.pacs_port,
        ),
        local_ae=LocalAEConfig(
            calling_aet=settings.local_calling_aet,
            modality=settings.local_modality,
            resize_max=settings.local_resize_max,
            transfer_syntax=settings.local_transfer_syntax,
            charset=settings.local_charset,
        ),
        flags=FlagsConfig(
            include_patient_info_except_id=settings.flag_include_patient_info_except_id,
            include_exam_description=settings.flag_include_exam_description,
            theme_dark=settings.flag_theme_dark,
        ),
        dicomweb=DicomwebConfig(
            base_url=settings.dicomweb_base_url,
            verify_tls=settings.dicomweb_verify_tls,
            timeout=settings.dicomweb_timeout_s,
        ),
    )


def _merge_dicts(defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(defaults.get(key), dict):
            defaults[key] = _merge_dicts(defaults[key], value)
        else:
            defaults[key] = value
    return defaults


class SettingsStore:
    def __init__(self, path: Path, defaults: RuntimeSettings) -> None:
        self.path = path
        self.defaults = defaults

    def load(self) -> RuntimeSettings:
        if not self.path.exists():
            return self.defaults
        data = json.loads(self.path.read_text(encoding="utf-8"))
        merged = _merge_dicts(self.defaults.model_dump(by_alias=True), data)
        return RuntimeSettings.model_validate(merged)

    def save(self, settings: RuntimeSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(settings.model_dump(by_alias=True), ensure_ascii=False, indent=2)
        self.path.write_text(payload, encoding="utf-8")
