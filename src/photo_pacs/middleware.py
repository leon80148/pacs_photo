from __future__ import annotations

import uuid
from typing import Callable

from fastapi import Request, Response

from photo_pacs.metrics import metrics


async def request_id_middleware(request: Request, call_next: Callable) -> Response:
    header_name = getattr(request.app.state, "request_id_header", "X-Request-ID")
    request_id = request.headers.get(header_name) or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers[header_name] = request_id
    return response


async def metrics_middleware(request: Request, call_next: Callable) -> Response:
    response = await call_next(request)
    metrics.inc("requests_total")
    return response
