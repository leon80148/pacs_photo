from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from photo_pacs.api.routes.pacs import router as pacs_router
from photo_pacs.api.routes.settings import router as settings_router
from photo_pacs.api.routes.studies import router as studies_router
from photo_pacs.api.schemas import HealthResponse, MetricsResponse
from photo_pacs.logging import configure_logging, get_logger
from photo_pacs.metrics import metrics
from photo_pacs.middleware import metrics_middleware, request_id_middleware
from photo_pacs.settings import get_settings


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(title="photo_pacs", version="0.1.0")
    app.state.settings = settings
    app.state.request_id_header = settings.request_id_header

    app.middleware("http")(request_id_middleware)
    app.middleware("http")(metrics_middleware)

    app.include_router(studies_router)
    app.include_router(pacs_router)
    app.include_router(settings_router)

    @app.get("/healthz", response_model=HealthResponse)
    async def healthz() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/metrics", response_model=MetricsResponse)
    async def metrics_endpoint() -> MetricsResponse:
        return MetricsResponse(counts=metrics.snapshot())

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        metrics.inc("errors_total")
        payload = exc.detail
        if isinstance(payload, str):
            payload = {"code": payload}
        payload["requestId"] = request_id
        return JSONResponse(
            status_code=exc.status_code,
            content=payload,
            headers={settings.request_id_header: request_id or ""},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        metrics.inc("errors_total")
        return JSONResponse(
            status_code=400,
            content={"code": "VALIDATION_ERROR", "requestId": request_id},
            headers={settings.request_id_header: request_id or ""},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger = get_logger("photo_pacs")
        request_id = getattr(request.state, "request_id", None)
        logger.error(
            "unhandled_exception",
            extra={"request_id": request_id},
            exc_info=exc,
        )
        metrics.inc("errors_total")
        return JSONResponse(
            status_code=500,
            content={"code": "INTERNAL_ERROR", "requestId": request_id},
            headers={settings.request_id_header: request_id or ""},
        )

    app.mount("/", StaticFiles(directory="web", html=True), name="web")

    return app


app = create_app()
