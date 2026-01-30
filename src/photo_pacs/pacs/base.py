from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from pydicom.dataset import Dataset


@dataclass
class PacsInstanceResult:
    index: int
    sop_instance_uid: str
    status: str
    detail: str | None = None


@dataclass
class PacsBatchResult:
    status: str
    instances: list[PacsInstanceResult]
    error_code: str | None = None
    detail: str | None = None


@dataclass
class PacsEchoResult:
    status: str
    message: str
    error_code: str | None = None


class PacsSender(Protocol):
    def send_instances(self, datasets: list[Dataset]) -> PacsBatchResult:
        raise NotImplementedError

    def echo(self) -> PacsEchoResult:
        raise NotImplementedError
