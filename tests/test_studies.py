from __future__ import annotations

from io import BytesIO

import pydicom
from PIL import Image


def _make_image_bytes() -> BytesIO:
    buffer = BytesIO()
    image = Image.new("RGB", (8, 8), color=(255, 0, 0))
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer


def test_create_study_success_multi_image(make_client):
    client, settings = make_client()

    files = [
        ("images[]", ("one.jpg", _make_image_bytes(), "image/jpeg")),
        ("images[]", ("two.jpg", _make_image_bytes(), "image/jpeg")),
    ]
    response = client.post(
        "/api/studies",
        files=files,
        data={"patientId": "P-001"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["studyInstanceUID"]
    assert payload["seriesInstanceUID"]
    assert len(payload["instances"]) == 2

    dicom_files = list(settings.dicom_dir.glob("*.dcm"))
    assert len(dicom_files) == 2
    datasets = [pydicom.dcmread(str(path)) for path in dicom_files]
    study_uids = {ds.StudyInstanceUID for ds in datasets}
    series_uids = {ds.SeriesInstanceUID for ds in datasets}
    instance_numbers = {int(ds.InstanceNumber) for ds in datasets}

    assert len(study_uids) == 1
    assert len(series_uids) == 1
    assert instance_numbers == {1, 2}
    assert all(ds.PatientID == "P-001" for ds in datasets)


def test_create_study_invalid_image(make_client):
    client, _ = make_client()

    files = [("images[]", ("bad.txt", BytesIO(b"bad"), "text/plain"))]
    response = client.post("/api/studies", files=files, data={"patientId": "P-9"})

    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "VALIDATION_ERROR"
