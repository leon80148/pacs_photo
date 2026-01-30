from __future__ import annotations

from pydicom.dataset import Dataset

from photo_pacs.pacs.base import PacsBatchResult, PacsEchoResult, PacsInstanceResult


class MockPacsSender:
    def send_instances(self, datasets: list[Dataset]) -> PacsBatchResult:
        instances = [
            PacsInstanceResult(
                index=index,
                sop_instance_uid=dataset.SOPInstanceUID,
                status="stored",
            )
            for index, dataset in enumerate(datasets, start=1)
        ]
        return PacsBatchResult(status="success", instances=instances)

    def echo(self) -> PacsEchoResult:
        return PacsEchoResult(status="success", message="C-ECHO OK")
