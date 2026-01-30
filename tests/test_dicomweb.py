from __future__ import annotations

import httpx
import respx
from pydicom.dataset import Dataset
from pydicom.uid import generate_uid

from photo_pacs.pacs.dicomweb import DicomwebPacsSender

BASE_URL = "https://pacs.example.com/dcm4chee-arc/aets/DCM4CHEE/rs"


def _make_dataset() -> Dataset:
    ds = Dataset()
    ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.7"
    ds.SOPInstanceUID = generate_uid()
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.PatientID = "TEST001"
    ds.Modality = "OT"
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.SamplesPerPixel = 1
    ds.Rows = 1
    ds.Columns = 1
    ds.PixelRepresentation = 0
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelData = b"\x00"
    ds.is_little_endian = True
    ds.is_implicit_VR = True
    return ds


def _make_sender() -> DicomwebPacsSender:
    return DicomwebPacsSender(base_url=BASE_URL, verify_tls=False, timeout=10)


def _stow_success_json(datasets: list[Dataset]) -> dict:
    return {
        "00081199": {
            "vr": "SQ",
            "Value": [
                {
                    "00081150": {"vr": "UI", "Value": [ds.SOPClassUID]},
                    "00081155": {"vr": "UI", "Value": [ds.SOPInstanceUID]},
                }
                for ds in datasets
            ],
        }
    }


@respx.mock
def test_send_success():
    sender = _make_sender()
    datasets = [_make_dataset(), _make_dataset()]

    respx.post(f"{BASE_URL}/studies").mock(
        return_value=httpx.Response(200, json=_stow_success_json(datasets))
    )

    result = sender.send_instances(datasets)
    assert result.status == "success"
    assert len(result.instances) == 2
    assert all(inst.status == "stored" for inst in result.instances)
    assert result.error_code is None


def test_send_empty():
    sender = _make_sender()
    result = sender.send_instances([])
    assert result.status == "success"
    assert result.instances == []


@respx.mock
def test_send_timeout():
    sender = _make_sender()
    datasets = [_make_dataset()]

    respx.post(f"{BASE_URL}/studies").mock(side_effect=httpx.ReadTimeout("timeout"))

    result = sender.send_instances(datasets)
    assert result.status == "failed"
    assert result.error_code == "PACS_TIMEOUT"
    assert len(result.instances) == 1
    assert result.instances[0].status == "failed"


@respx.mock
def test_send_connection_error():
    sender = _make_sender()
    datasets = [_make_dataset()]

    respx.post(f"{BASE_URL}/studies").mock(
        side_effect=httpx.ConnectError("connection refused")
    )

    result = sender.send_instances(datasets)
    assert result.status == "failed"
    assert result.error_code == "PACS_REJECTED"
    assert result.instances[0].detail == "connection_error"


@respx.mock
def test_send_http_500():
    sender = _make_sender()
    datasets = [_make_dataset()]

    respx.post(f"{BASE_URL}/studies").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    result = sender.send_instances(datasets)
    assert result.status == "failed"
    assert result.error_code == "PACS_REJECTED"
    assert result.instances[0].detail == "http_500"


@respx.mock
def test_send_http_409_partial():
    sender = _make_sender()
    ds1 = _make_dataset()
    ds2 = _make_dataset()
    datasets = [ds1, ds2]

    response_json = {
        "00081199": {
            "vr": "SQ",
            "Value": [
                {
                    "00081150": {"vr": "UI", "Value": [ds1.SOPClassUID]},
                    "00081155": {"vr": "UI", "Value": [ds1.SOPInstanceUID]},
                }
            ],
        },
        "00081198": {
            "vr": "SQ",
            "Value": [
                {
                    "00081150": {"vr": "UI", "Value": [ds2.SOPClassUID]},
                    "00081155": {"vr": "UI", "Value": [ds2.SOPInstanceUID]},
                }
            ],
        },
    }

    respx.post(f"{BASE_URL}/studies").mock(
        return_value=httpx.Response(409, json=response_json)
    )

    result = sender.send_instances(datasets)
    assert result.status == "partial"
    assert result.error_code == "PACS_REJECTED"
    assert result.instances[0].status == "stored"
    assert result.instances[1].status == "failed"


@respx.mock
def test_send_unparseable_response():
    sender = _make_sender()
    datasets = [_make_dataset()]

    respx.post(f"{BASE_URL}/studies").mock(
        return_value=httpx.Response(200, text="not json at all")
    )

    result = sender.send_instances(datasets)
    assert result.status == "success"
    assert len(result.instances) == 1
    assert result.instances[0].status == "stored"


@respx.mock
def test_echo_success():
    sender = _make_sender()

    respx.get(f"{BASE_URL}/studies").mock(
        return_value=httpx.Response(200, json=[])
    )

    result = sender.echo()
    assert result.status == "success"
    assert result.message == "DICOMweb QIDO-RS OK"


@respx.mock
def test_echo_timeout():
    sender = _make_sender()

    respx.get(f"{BASE_URL}/studies").mock(
        side_effect=httpx.ReadTimeout("timeout")
    )

    result = sender.echo()
    assert result.status == "failure"
    assert result.error_code == "PACS_TIMEOUT"


@respx.mock
def test_echo_connection_error():
    sender = _make_sender()

    respx.get(f"{BASE_URL}/studies").mock(
        side_effect=httpx.ConnectError("connection refused")
    )

    result = sender.echo()
    assert result.status == "failure"
    assert result.error_code == "PACS_REJECTED"


@respx.mock
def test_echo_http_error():
    sender = _make_sender()

    respx.get(f"{BASE_URL}/studies").mock(
        return_value=httpx.Response(401, text="Unauthorized")
    )

    result = sender.echo()
    assert result.status == "failure"
    assert result.error_code == "PACS_REJECTED"
    assert "401" in result.message
