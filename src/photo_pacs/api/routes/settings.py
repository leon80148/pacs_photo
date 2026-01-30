from __future__ import annotations

from fastapi import APIRouter, Depends

from photo_pacs.api.schemas import SettingsResponse
from photo_pacs.services.settings_store import (
    RuntimeSettings,
    SettingsStore,
    build_default_runtime_settings,
)
from photo_pacs.settings import Settings, get_settings


router = APIRouter()


def _store(settings: Settings) -> SettingsStore:
    return SettingsStore(
        settings.settings_path,
        build_default_runtime_settings(settings),
    )


@router.get("/api/settings/info")
async def get_settings_info(
    settings: Settings = Depends(get_settings),
) -> dict:
    return {"pacsBackend": settings.pacs_backend}


@router.get("/api/settings", response_model=SettingsResponse)
async def get_settings_endpoint(
    settings: Settings = Depends(get_settings),
) -> SettingsResponse:
    store = _store(settings)
    return SettingsResponse(settings=store.load())


@router.put("/api/settings", response_model=SettingsResponse)
async def update_settings_endpoint(
    payload: RuntimeSettings, settings: Settings = Depends(get_settings)
) -> SettingsResponse:
    store = _store(settings)
    store.save(payload)
    return SettingsResponse(settings=payload)
