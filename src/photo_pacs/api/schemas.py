from __future__ import annotations

from pydantic import BaseModel, Field

from photo_pacs.services.settings_store import RuntimeSettings


class InstanceStatus(BaseModel):
    index: int
    sop_instance_uid: str = Field(alias="sopInstanceUID")
    status: str

    model_config = {"populate_by_name": True}


class PacsInfo(BaseModel):
    called_aet: str = Field(alias="calledAET")
    host: str
    port: int

    model_config = {"populate_by_name": True}


class StudyResponse(BaseModel):
    status: str
    study_instance_uid: str = Field(alias="studyInstanceUID")
    series_instance_uid: str = Field(alias="seriesInstanceUID")
    instances: list[InstanceStatus]
    pacs: PacsInfo

    model_config = {"populate_by_name": True}


class PacsEchoRequest(BaseModel):
    called_aet: str = Field(alias="calledAET")
    host: str
    port: int
    calling_aet: str = Field(alias="callingAET")

    model_config = {"populate_by_name": True}


class PacsEchoResponse(BaseModel):
    status: str
    message: str
    code: str | None = None


class SettingsResponse(BaseModel):
    settings: RuntimeSettings


class PatientIdOcrResponse(BaseModel):
    status: str
    patient_id: str = Field(alias="patientId")
    backend: str
    checksum_valid: bool = Field(default=False, alias="checksumValid")
    elapsed_ms: int = Field(default=0, alias="elapsedMs")

    model_config = {"populate_by_name": True}


class HealthResponse(BaseModel):
    status: str


class MetricsResponse(BaseModel):
    counts: dict[str, int]
