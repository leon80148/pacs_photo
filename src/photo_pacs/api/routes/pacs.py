from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from photo_pacs.api.schemas import PacsEchoRequest, PacsEchoResponse
from photo_pacs.metrics import metrics
from photo_pacs.pacs import get_pacs_sender
from photo_pacs.pacs.cstore import CStorePacsSender
from photo_pacs.pacs.mock import MockPacsSender
from photo_pacs.services.settings_store import (
    SettingsStore,
    build_default_runtime_settings,
)
from photo_pacs.settings import Settings, get_settings

router = APIRouter()


@router.post("/api/pacs/echo", response_model=PacsEchoResponse)
async def pacs_echo(
    payload: PacsEchoRequest, settings: Settings = Depends(get_settings)
) -> PacsEchoResponse:
    settings_store = SettingsStore(
        settings.settings_path,
        build_default_runtime_settings(settings),
    )
    runtime_settings = settings_store.load()

    if settings.pacs_backend == "mock":
        result = MockPacsSender().echo()
    elif settings.pacs_backend == "cstore":
        sender = CStorePacsSender(
            host=payload.host,
            port=payload.port,
            pacs_ae_title=payload.called_aet,
            local_ae_title=payload.calling_aet,
            use_tls=settings.pacs_tls,
            tls_ca_file=settings.pacs_tls_ca_file,
            tls_cert_file=settings.pacs_tls_cert_file,
            tls_key_file=settings.pacs_tls_key_file,
        )
        result = sender.echo()
    else:
        sender = get_pacs_sender(settings, runtime_settings)
        result = sender.echo()

    if result.status != "success":
        metrics.inc("pacs_error")
        code = result.error_code or "PACS_REJECTED"
        status_code = 504 if code == "PACS_TIMEOUT" else 502
        raise HTTPException(status_code=status_code, detail=code)

    return PacsEchoResponse(status="success", message=result.message)
