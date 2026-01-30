from __future__ import annotations

from photo_pacs.his.base import HisClient, HisPatient


class MockHisClient(HisClient):
    def lookup_by_chart_no(self, chart_no: str) -> HisPatient:
        return HisPatient(patient_id=f"MOCK-{chart_no}")
