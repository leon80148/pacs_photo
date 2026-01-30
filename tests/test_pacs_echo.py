from __future__ import annotations


def test_pacs_echo_success(make_client):
    client, _ = make_client()

    response = client.post(
        "/api/pacs/echo",
        json={
            "calledAET": "PACS",
            "host": "127.0.0.1",
            "port": 104,
            "callingAET": "PHONE",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"


def test_pacs_echo_dicomweb_no_url(make_client):
    client, _ = make_client(overrides={"pacs_backend": "dicomweb"})

    response = client.post(
        "/api/pacs/echo",
        json={
            "calledAET": "PACS",
            "host": "127.0.0.1",
            "port": 104,
            "callingAET": "PHONE",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
