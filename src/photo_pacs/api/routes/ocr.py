from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from photo_pacs.api.schemas import PatientIdOcrResponse
from photo_pacs.metrics import metrics
from photo_pacs.services.patient_id_ocr import (
    OcrBackendUnavailableError,
    recognize_patient_id_from_image,
)
from photo_pacs.settings import Settings, get_settings

router = APIRouter()


@router.post("/api/patient-id/ocr", response_model=PatientIdOcrResponse)
async def recognize_patient_id(
    card_image: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> PatientIdOcrResponse:
    if not card_image.content_type or not card_image.content_type.startswith("image/"):
        metrics.inc("validation_error")
        raise HTTPException(status_code=400, detail="VALIDATION_ERROR")

    image_bytes = await card_image.read()
    if not image_bytes:
        metrics.inc("validation_error")
        raise HTTPException(status_code=400, detail="VALIDATION_ERROR")

    try:
        result = await asyncio.to_thread(
            recognize_patient_id_from_image,
            image_bytes,
            settings.ocr_det_side_len,
            settings.ocr_version,
        )
    except OcrBackendUnavailableError as exc:
        metrics.inc("ocr_backend_unavailable")
        raise HTTPException(status_code=503, detail="OCR_UNAVAILABLE") from exc

    if not result.patient_id:
        metrics.inc("ocr_not_found")
        raise HTTPException(status_code=422, detail="PATIENT_ID_NOT_FOUND")

    return PatientIdOcrResponse(
        status="success",
        patient_id=result.patient_id,
        backend=result.backend,
        checksum_valid=getattr(result, "checksum_valid", False),
        elapsed_ms=getattr(result, "elapsed_ms", 0),
    )
