from __future__ import annotations

import re
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydicom.uid import generate_uid

from photo_pacs.api.schemas import InstanceStatus, PacsInfo, StudyResponse
from photo_pacs.logging import get_logger
from photo_pacs.metrics import metrics
from photo_pacs.pacs import get_pacs_sender
from photo_pacs.services.conversion import (
    ConversionConfig,
    ConversionError,
    ExamInfo,
    PatientInfo,
    image_to_dicom,
)
from photo_pacs.services.settings_store import (
    SettingsStore,
    build_default_runtime_settings,
)
from photo_pacs.settings import Settings, get_settings
from photo_pacs.storage.local import LocalFileStore

router = APIRouter()
logger = get_logger("photo_pacs.studies")


def _get_form_value(form, key: str) -> str | None:
    value = form.get(key)
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return None


def _parse_exam_datetime(raw: str | None) -> datetime:
    if not raw:
        return datetime.now()
    value = raw.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="VALIDATION_ERROR") from exc
    if dt.tzinfo:
        dt = dt.replace(tzinfo=None)
    return dt


@router.post("/api/studies", response_model=StudyResponse, status_code=status.HTTP_200_OK)
async def create_study(request: Request, settings: Settings = Depends(get_settings)) -> StudyResponse:
    request_id = getattr(request.state, "request_id", "")
    form = await request.form()

    images = list(form.getlist("images"))
    if not images:
        images = list(form.getlist("images[]"))
    if not images:
        metrics.inc("validation_error")
        raise HTTPException(status_code=400, detail="VALIDATION_ERROR")

    patient_id = _get_form_value(form, "patientId")
    patient_name = _get_form_value(form, "patientName")
    birth_date = _get_form_value(form, "birthDate")
    sex = _get_form_value(form, "sex")
    exam_datetime = _parse_exam_datetime(_get_form_value(form, "examDateTime"))
    exam_description = _get_form_value(form, "examDescription")

    if sex and sex not in {"M", "F", "O", "U"}:
        metrics.inc("validation_error")
        raise HTTPException(status_code=400, detail="VALIDATION_ERROR")
    if birth_date and not re.match(r"^\d{4}-\d{2}-\d{2}$", birth_date):
        metrics.inc("validation_error")
        raise HTTPException(status_code=400, detail="VALIDATION_ERROR")

    if not patient_id:
        metrics.inc("validation_error")
        raise HTTPException(status_code=400, detail="VALIDATION_ERROR")

    settings_store = SettingsStore(
        settings.settings_path,
        build_default_runtime_settings(settings),
    )
    runtime_settings = settings_store.load()

    upload_id = str(uuid4())
    store = LocalFileStore(settings.upload_dir, settings.dicom_dir)
    original_paths = []
    dicom_paths = []
    datasets = []

    conversion_config = ConversionConfig(
        modality=runtime_settings.local_ae.modality,
        resize_max=runtime_settings.local_ae.resize_max,
        transfer_syntax=runtime_settings.local_ae.transfer_syntax,
        charset=runtime_settings.local_ae.charset,
        include_patient_info_except_id=runtime_settings.flags.include_patient_info_except_id,
        include_exam_description=runtime_settings.flags.include_exam_description,
    )
    patient_info = PatientInfo(
        patient_id=patient_id,
        patient_name=patient_name,
        birth_date=birth_date,
        sex=sex,
    )
    exam_info = ExamInfo(
        exam_datetime=exam_datetime,
        exam_description=exam_description,
    )

    study_uid = generate_uid()
    series_uid = generate_uid()

    try:
        for index, upload in enumerate(images, start=1):
            original_path = store.save_upload(upload_id, upload, index)
            if original_path.stat().st_size > settings.max_upload_mb * 1024 * 1024:
                metrics.inc("upload_too_large")
                raise HTTPException(status_code=400, detail="VALIDATION_ERROR")
            original_paths.append(original_path)

        for index, original_path in enumerate(original_paths, start=1):
            dataset = image_to_dicom(
                original_path,
                patient_info,
                exam_info,
                study_uid,
                series_uid,
                index,
                conversion_config,
            )
            dicom_path = store.save_dicom(f"{upload_id}_{index}", dataset)
            dicom_paths.append(dicom_path)
            datasets.append(dataset)
    except ConversionError as exc:
        metrics.inc("conversion_error")
        store.cleanup(original_paths + dicom_paths)
        raise HTTPException(status_code=400, detail="VALIDATION_ERROR") from exc
    except HTTPException:
        store.cleanup(original_paths + dicom_paths)
        raise

    sender = get_pacs_sender(settings, runtime_settings)
    send_result = sender.send_instances(datasets)

    if send_result.status != "success":
        metrics.inc("pacs_error")
        logger.info(
            "pacs_send_failed",
            extra={
                "request_id": request_id,
                "upload_id": upload_id,
                "backend": settings.pacs_backend,
            },
        )
        error_code = send_result.error_code or "PACS_REJECTED"
        status_code = 504 if error_code == "PACS_TIMEOUT" else 502
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": error_code,
                "instances": [
                    {
                        "index": item.index,
                        "sopInstanceUID": item.sop_instance_uid,
                        "status": item.status,
                    }
                    for item in send_result.instances
                ],
            },
        )

    if not settings.keep_files_on_success:
        store.cleanup(original_paths + dicom_paths)

    logger.info(
        "study_uploaded",
        extra={
            "request_id": request_id,
            "upload_id": upload_id,
            "backend": settings.pacs_backend,
        },
    )

    return StudyResponse(
        status="success",
        study_instance_uid=study_uid,
        series_instance_uid=series_uid,
        instances=[
            InstanceStatus(
                index=item.index,
                sop_instance_uid=item.sop_instance_uid,
                status=item.status,
            )
            for item in send_result.instances
        ],
        pacs=PacsInfo(
            called_aet=runtime_settings.pacs.called_aet,
            host=runtime_settings.pacs.host,
            port=runtime_settings.pacs.port,
        ),
    )
