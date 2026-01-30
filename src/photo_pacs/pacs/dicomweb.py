from __future__ import annotations

import io
import logging
import uuid

import httpx
from pydicom.dataset import Dataset
from pydicom.filewriter import dcmwrite

from photo_pacs.pacs.base import PacsBatchResult, PacsEchoResult, PacsInstanceResult

logger = logging.getLogger(__name__)


class DicomwebPacsSender:
    def __init__(
        self,
        base_url: str,
        verify_tls: bool = True,
        timeout: int = 30,
        auth: httpx.Auth | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.verify_tls = verify_tls
        self.timeout = timeout
        self.auth = auth

    def _build_multipart_body(
        self, datasets: list[Dataset], boundary: str
    ) -> bytes:
        parts: list[bytes] = []
        for ds in datasets:
            buf = io.BytesIO()
            dcmwrite(buf, ds, write_like_original=False)
            part_bytes = buf.getvalue()
            parts.append(
                f"--{boundary}\r\n"
                f"Content-Type: application/dicom\r\n"
                f"\r\n".encode("ascii")
                + part_bytes
                + b"\r\n"
            )
        parts.append(f"--{boundary}--\r\n".encode("ascii"))
        return b"".join(parts)

    def _parse_store_response(
        self, response: httpx.Response, datasets: list[Dataset]
    ) -> list[PacsInstanceResult]:
        try:
            body = response.json()
        except Exception:
            return [
                PacsInstanceResult(
                    index=i + 1,
                    sop_instance_uid=ds.SOPInstanceUID,
                    status="stored",
                )
                for i, ds in enumerate(datasets)
            ]

        stored_uids: set[str] = set()
        ref_seq = body.get("00081199", {}).get("Value", [])
        for item in ref_seq:
            uid_entry = item.get("00081155", {})
            uid_val = uid_entry.get("Value", [None])[0]
            if uid_val:
                stored_uids.add(uid_val)

        failed_uids: set[str] = set()
        fail_seq = body.get("00081198", {}).get("Value", [])
        for item in fail_seq:
            uid_entry = item.get("00081155", {})
            uid_val = uid_entry.get("Value", [None])[0]
            if uid_val:
                failed_uids.add(uid_val)

        instances: list[PacsInstanceResult] = []
        for i, ds in enumerate(datasets):
            uid = ds.SOPInstanceUID
            if uid in failed_uids:
                instances.append(
                    PacsInstanceResult(
                        index=i + 1,
                        sop_instance_uid=uid,
                        status="failed",
                        detail="rejected_by_server",
                    )
                )
            else:
                instances.append(
                    PacsInstanceResult(
                        index=i + 1,
                        sop_instance_uid=uid,
                        status="stored",
                    )
                )
        return instances

    def send_instances(self, datasets: list[Dataset]) -> PacsBatchResult:
        if not datasets:
            return PacsBatchResult(status="success", instances=[])

        boundary = uuid.uuid4().hex
        body = self._build_multipart_body(datasets, boundary)
        content_type = (
            f"multipart/related; "
            f'type="application/dicom"; '
            f"boundary={boundary}"
        )

        try:
            with httpx.Client(
                verify=self.verify_tls,
                timeout=self.timeout,
                auth=self.auth,
            ) as client:
                response = client.post(
                    f"{self.base_url}/studies",
                    content=body,
                    headers={"Content-Type": content_type},
                )
        except httpx.TimeoutException:
            logger.warning("STOW-RS timeout: %s", self.base_url)
            return PacsBatchResult(
                status="failed",
                instances=[
                    PacsInstanceResult(
                        index=i + 1,
                        sop_instance_uid=ds.SOPInstanceUID,
                        status="failed",
                        detail="timeout",
                    )
                    for i, ds in enumerate(datasets)
                ],
                error_code="PACS_TIMEOUT",
            )
        except httpx.HTTPError as exc:
            logger.warning("STOW-RS connection error: %s", exc)
            return PacsBatchResult(
                status="failed",
                instances=[
                    PacsInstanceResult(
                        index=i + 1,
                        sop_instance_uid=ds.SOPInstanceUID,
                        status="failed",
                        detail="connection_error",
                    )
                    for i, ds in enumerate(datasets)
                ],
                error_code="PACS_REJECTED",
            )

        logger.info(
            "STOW-RS response %d: %s",
            response.status_code,
            response.text[:500],
        )

        if response.status_code == 409:
            instances = self._parse_store_response(response, datasets)
            return PacsBatchResult(
                status="partial",
                instances=instances,
                error_code="PACS_REJECTED",
            )

        if response.status_code >= 400:
            logger.warning(
                "STOW-RS HTTP %d: %s", response.status_code, response.text[:200]
            )
            return PacsBatchResult(
                status="failed",
                instances=[
                    PacsInstanceResult(
                        index=i + 1,
                        sop_instance_uid=ds.SOPInstanceUID,
                        status="failed",
                        detail=f"http_{response.status_code}",
                    )
                    for i, ds in enumerate(datasets)
                ],
                error_code="PACS_REJECTED",
            )

        instances = self._parse_store_response(response, datasets)
        if any(inst.status != "stored" for inst in instances):
            return PacsBatchResult(
                status="partial",
                instances=instances,
                error_code="PACS_REJECTED",
            )
        return PacsBatchResult(status="success", instances=instances)

    def echo(self) -> PacsEchoResult:
        try:
            with httpx.Client(
                verify=self.verify_tls,
                timeout=self.timeout,
                auth=self.auth,
            ) as client:
                response = client.get(
                    f"{self.base_url}/studies",
                    params={"limit": 1},
                )
        except httpx.TimeoutException:
            return PacsEchoResult(
                status="failure",
                message="DICOMweb connection timeout",
                error_code="PACS_TIMEOUT",
            )
        except httpx.HTTPError as exc:
            return PacsEchoResult(
                status="failure",
                message=f"DICOMweb connection error: {exc}",
                error_code="PACS_REJECTED",
            )

        if response.status_code == 200:
            return PacsEchoResult(
                status="success",
                message="DICOMweb QIDO-RS OK",
            )
        return PacsEchoResult(
            status="failure",
            message=f"DICOMweb HTTP {response.status_code}",
            error_code="PACS_REJECTED",
        )
