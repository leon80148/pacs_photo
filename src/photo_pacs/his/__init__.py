from __future__ import annotations

from photo_pacs.his.base import HisClient, HisNotFound, HisPatient, HisUnavailable
from photo_pacs.his.http import HttpHisClient
from photo_pacs.his.mock import MockHisClient
from photo_pacs.services.settings_store import RuntimeSettings
from photo_pacs.settings import Settings


def get_his_client(settings: Settings, runtime_settings: RuntimeSettings) -> HisClient:
    if settings.his_backend == "http":
        if not runtime_settings.his.base_url:
            return MockHisClient()
        return HttpHisClient(
            base_url=runtime_settings.his.base_url,
            api_key=runtime_settings.his.api_key,
            timeout=runtime_settings.his.timeout,
            retry=runtime_settings.his.retry,
        )
    return MockHisClient()
