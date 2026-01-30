from __future__ import annotations

import httpx

from photo_pacs.pacs.base import PacsSender
from photo_pacs.pacs.cstore import CStorePacsSender
from photo_pacs.pacs.dicomweb import DicomwebPacsSender
from photo_pacs.pacs.mock import MockPacsSender
from photo_pacs.services.settings_store import RuntimeSettings
from photo_pacs.settings import Settings


class BearerAuth(httpx.Auth):
    def __init__(self, token: str) -> None:
        self.token = token

    def auth_flow(self, request: httpx.Request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


def _build_dicomweb_auth(settings: Settings) -> httpx.Auth | None:
    method = settings.dicomweb_auth_method
    if method == "basic" and settings.dicomweb_username:
        return httpx.BasicAuth(
            username=settings.dicomweb_username,
            password=settings.dicomweb_password or "",
        )
    if method == "bearer" and settings.dicomweb_token:
        return BearerAuth(settings.dicomweb_token)
    return None


def get_pacs_sender(
    settings: Settings, runtime_settings: RuntimeSettings
) -> PacsSender:
    if settings.pacs_backend == "cstore":
        return CStorePacsSender(
            host=runtime_settings.pacs.host,
            port=runtime_settings.pacs.port,
            pacs_ae_title=runtime_settings.pacs.called_aet,
            local_ae_title=runtime_settings.local_ae.calling_aet,
            use_tls=settings.pacs_tls,
            tls_ca_file=settings.pacs_tls_ca_file,
            tls_cert_file=settings.pacs_tls_cert_file,
            tls_key_file=settings.pacs_tls_key_file,
        )
    if settings.pacs_backend == "dicomweb":
        base_url = runtime_settings.dicomweb.base_url or settings.dicomweb_base_url
        if not base_url:
            return MockPacsSender()
        auth = _build_dicomweb_auth(settings)
        return DicomwebPacsSender(
            base_url=base_url,
            verify_tls=runtime_settings.dicomweb.verify_tls,
            timeout=runtime_settings.dicomweb.timeout,
            auth=auth,
        )
    return MockPacsSender()
