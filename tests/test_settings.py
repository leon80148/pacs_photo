from __future__ import annotations


def test_get_settings_returns_defaults(make_client):
    client, _ = make_client()

    response = client.get("/api/settings")
    assert response.status_code == 200
    payload = response.json()
    assert payload["settings"]["pacs"]["calledAET"]
    assert payload["settings"]["localAE"]["callingAET"]


def test_update_settings(make_client):
    client, _ = make_client()

    update_payload = {
        "pacs": {"calledAET": "PACS_AE", "host": "10.0.0.2", "port": 11112},
        "localAE": {
            "callingAET": "PHONE_AE",
            "modality": "OT",
            "resizeMax": 800,
            "transferSyntax": "1.2.840.10008.1.2",
            "charset": "ISO_IR 192",
        },
        "flags": {
            "includePatientInfoExceptId": False,
            "includeExamDescription": False,
            "themeDark": True,
        },
    }

    response = client.put("/api/settings", json=update_payload)
    assert response.status_code == 200

    response = client.get("/api/settings")
    payload = response.json()
    assert payload["settings"]["pacs"]["calledAET"] == "PACS_AE"
