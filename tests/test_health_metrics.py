from __future__ import annotations

from fastapi.testclient import TestClient

from photo_pacs.main import create_app


def test_healthz_ok():
    client = TestClient(create_app())
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics_ok():
    client = TestClient(create_app())
    response = client.get("/metrics")
    assert response.status_code == 200
    assert isinstance(response.json().get("counts"), dict)
