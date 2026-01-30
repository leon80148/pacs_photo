from __future__ import annotations

import ssl
from pathlib import Path
from typing import Iterable

from pydicom.dataset import Dataset
from pynetdicom import AE
from pynetdicom.sop_class import SecondaryCaptureImageStorage, Verification

from photo_pacs.pacs.base import PacsBatchResult, PacsEchoResult, PacsInstanceResult


class CStorePacsSender:
    def __init__(
        self,
        host: str,
        port: int,
        pacs_ae_title: str,
        local_ae_title: str,
        use_tls: bool,
        tls_ca_file: Path | None,
        tls_cert_file: Path | None,
        tls_key_file: Path | None,
    ) -> None:
        self.host = host
        self.port = port
        self.pacs_ae_title = pacs_ae_title
        self.local_ae_title = local_ae_title
        self.use_tls = use_tls
        self.tls_ca_file = tls_ca_file
        self.tls_cert_file = tls_cert_file
        self.tls_key_file = tls_key_file

    def _build_tls_args(self) -> tuple | None:
        if not self.use_tls:
            return None
        context = ssl.create_default_context(
            ssl.Purpose.SERVER_AUTH,
            cafile=str(self.tls_ca_file) if self.tls_ca_file else None,
        )
        if self.tls_cert_file and self.tls_key_file:
            context.load_cert_chain(
                certfile=str(self.tls_cert_file),
                keyfile=str(self.tls_key_file),
            )
        return (context, self.host)

    def _build_ae(self) -> AE:
        ae = AE(ae_title=self.local_ae_title)
        ae.add_requested_context(SecondaryCaptureImageStorage)
        ae.add_requested_context(Verification)
        return ae

    def _associate(self, ae: AE):
        return ae.associate(
            self.host,
            self.port,
            ae_title=self.pacs_ae_title,
            tls_args=self._build_tls_args(),
        )

    def _build_failed_instances(self, datasets: Iterable[Dataset], detail: str) -> list[PacsInstanceResult]:
        return [
            PacsInstanceResult(
                index=index,
                sop_instance_uid=dataset.SOPInstanceUID,
                status="failed",
                detail=detail,
            )
            for index, dataset in enumerate(datasets, start=1)
        ]

    def send_instances(self, datasets: list[Dataset]) -> PacsBatchResult:
        ae = self._build_ae()
        assoc = self._associate(ae)
        if not assoc.is_established:
            return PacsBatchResult(
                status="failed",
                instances=self._build_failed_instances(datasets, "association_failed"),
                error_code="PACS_REJECTED",
            )

        instances: list[PacsInstanceResult] = []
        timeout_detected = False
        try:
            for index, dataset in enumerate(datasets, start=1):
                status = assoc.send_c_store(dataset)
                if status and getattr(status, "Status", None) == 0x0000:
                    instances.append(
                        PacsInstanceResult(
                            index=index,
                            sop_instance_uid=dataset.SOPInstanceUID,
                            status="stored",
                        )
                    )
                else:
                    if status is None:
                        timeout_detected = True
                    instances.append(
                        PacsInstanceResult(
                            index=index,
                            sop_instance_uid=dataset.SOPInstanceUID,
                            status="failed",
                            detail="cstore_failed",
                        )
                    )
        finally:
            assoc.release()

        if any(item.status != "stored" for item in instances):
            return PacsBatchResult(
                status="partial",
                instances=instances,
                error_code="PACS_TIMEOUT" if timeout_detected else "PACS_REJECTED",
            )
        return PacsBatchResult(status="success", instances=instances)

    def echo(self) -> PacsEchoResult:
        ae = self._build_ae()
        assoc = self._associate(ae)
        if not assoc.is_established:
            return PacsEchoResult(
                status="failure",
                message="association_failed",
                error_code="PACS_REJECTED",
            )
        try:
            status = assoc.send_c_echo()
        finally:
            assoc.release()
        if status and getattr(status, "Status", None) == 0x0000:
            return PacsEchoResult(status="success", message="C-ECHO OK")
        return PacsEchoResult(
            status="failure",
            message="C-ECHO failed",
            error_code="PACS_TIMEOUT" if status is None else "PACS_REJECTED",
        )
