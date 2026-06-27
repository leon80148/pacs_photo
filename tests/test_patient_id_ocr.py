from __future__ import annotations

from io import BytesIO

from PIL import Image


def _make_image_bytes() -> BytesIO:
    buffer = BytesIO()
    image = Image.new("RGB", (24, 24), color=(255, 255, 255))
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer


def test_ocr_patient_id_success(make_client, monkeypatch):
    client, _ = make_client()

    def fake_recognize(
        _image_bytes: bytes, _det_side_len: int = 960, _ocr_version: str = "PPOCRV6"
    ):
        class Result:
            patient_id = "A123456789"
            backend = "rapidocr"

        return Result()

    monkeypatch.setattr(
        "photo_pacs.api.routes.ocr.recognize_patient_id_from_image",
        fake_recognize,
    )

    response = client.post(
        "/api/patient-id/ocr",
        files={"card_image": ("card.jpg", _make_image_bytes(), "image/jpeg")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["patientId"] == "A123456789"
    assert payload["backend"] == "rapidocr"


def test_ocr_patient_id_not_found(make_client, monkeypatch):
    client, _ = make_client()

    def fake_recognize(
        _image_bytes: bytes, _det_side_len: int = 960, _ocr_version: str = "PPOCRV6"
    ):
        class Result:
            patient_id = None
            backend = "rapidocr"

        return Result()

    monkeypatch.setattr(
        "photo_pacs.api.routes.ocr.recognize_patient_id_from_image",
        fake_recognize,
    )

    response = client.post(
        "/api/patient-id/ocr",
        files={"card_image": ("card.jpg", _make_image_bytes(), "image/jpeg")},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "PATIENT_ID_NOT_FOUND"
