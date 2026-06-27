"""可調參數：條碼掃描器設定 round-trip、OCR 解析度傳遞與耗時回傳。"""

from __future__ import annotations

from io import BytesIO

from PIL import Image


def _img() -> BytesIO:
    buf = BytesIO()
    Image.new("RGB", (16, 16), (255, 255, 255)).save(buf, format="JPEG")
    buf.seek(0)
    return buf


def _full_payload(scanner: dict) -> dict:
    # photo_pacs 的 PUT /api/settings 為完整取代語意，需送齊必填區塊。
    return {
        "pacs": {"calledAET": "PACS", "host": "127.0.0.1", "port": 104},
        "localAE": {
            "callingAET": "PHOTO_PACS",
            "modality": "OT",
            "resizeMax": 1024,
            "transferSyntax": "1.2.840.10008.1.2",
            "charset": "ISO_IR 192",
        },
        "flags": {
            "includePatientInfoExceptId": True,
            "includeExamDescription": True,
            "themeDark": True,
        },
        "scanner": scanner,
    }


def test_scanner_settings_present_in_defaults(make_client):
    client, _ = make_client()
    data = client.get("/api/settings").json()["settings"]
    assert data["scanner"]["roiHeightRatio"] == 0.4
    assert data["scanner"]["roiTargetWidth"] == 800
    assert data["scanner"]["detectIntervalMs"] == 100


def test_scanner_settings_round_trip(make_client):
    client, _ = make_client()
    resp = client.put(
        "/api/settings",
        json=_full_payload(
            {"roiHeightRatio": 0.3, "roiTargetWidth": 640, "detectIntervalMs": 50}
        ),
    )
    assert resp.status_code == 200
    data = client.get("/api/settings").json()["settings"]
    assert data["scanner"]["roiHeightRatio"] == 0.3
    assert data["scanner"]["roiTargetWidth"] == 640
    assert data["scanner"]["detectIntervalMs"] == 50


def test_scanner_settings_reject_out_of_range(make_client):
    client, _ = make_client()
    # roiHeightRatio 上限 1.0
    resp = client.put(
        "/api/settings",
        json=_full_payload(
            {"roiHeightRatio": 5, "roiTargetWidth": 640, "detectIntervalMs": 50}
        ),
    )
    assert resp.status_code == 400


def test_ocr_passes_configured_det_side_len(make_client, monkeypatch):
    client, _ = make_client({"ocr_det_side_len": 1280})
    captured = {}

    def fake_recognize(
        _image_bytes: bytes, det_side_len: int = 960, ocr_version: str = "PPOCRV6"
    ):
        captured["det_side_len"] = det_side_len
        captured["ocr_version"] = ocr_version

        class Result:
            patient_id = "A123456789"
            backend = "rapidocr"
            checksum_valid = True
            elapsed_ms = 321

        return Result()

    monkeypatch.setattr(
        "photo_pacs.api.routes.ocr.recognize_patient_id_from_image",
        fake_recognize,
    )

    resp = client.post(
        "/api/patient-id/ocr",
        files={"card_image": ("card.jpg", _img(), "image/jpeg")},
    )
    assert resp.status_code == 200
    assert captured["det_side_len"] == 1280
    assert resp.json()["elapsedMs"] == 321
