from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class HisPatient:
    patient_id: str
    name: str | None = None
    birth_date: str | None = None
    sex: str | None = None


class HisError(Exception):
    pass


class HisNotFound(HisError):
    pass


class HisUnavailable(HisError):
    pass


class HisClient(Protocol):
    def lookup_by_chart_no(self, chart_no: str) -> HisPatient:
        raise NotImplementedError
