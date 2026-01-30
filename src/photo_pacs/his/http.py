from __future__ import annotations

import httpx

from photo_pacs.his.base import HisClient, HisNotFound, HisPatient, HisUnavailable


def _convert_roc_date(roc_date: str | None) -> str | None:
    """民國年 YYYMMDD → 西元 YYYY-MM-DD"""
    if not roc_date or len(roc_date) < 5:
        return None
    try:
        roc_year = int(roc_date[:-4])
        month_day = roc_date[-4:]
        western_year = roc_year + 1911
        return f"{western_year}-{month_day[:2]}-{month_day[2:]}"
    except (ValueError, IndexError):
        return None


def _convert_sex(msex: str | None) -> str | None:
    """1=男→M, 2=女→F"""
    if msex == "1":
        return "M"
    if msex == "2":
        return "F"
    return None


class HttpHisClient(HisClient):
    def __init__(
        self,
        base_url: str,
        api_key: str | None,
        timeout: int,
        retry: int,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.retry = retry

    def lookup_by_chart_no(self, chart_no: str) -> HisPatient:
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        params = {"kcstmr": chart_no}
        last_error: Exception | None = None
        for _ in range(self.retry + 1):
            try:
                response = httpx.get(
                    f"{self.base_url}/api/patients/search",
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )
            except httpx.HTTPError as exc:
                last_error = exc
                continue

            if response.status_code == 401:
                raise HisUnavailable("his_auth_failed")
            if response.status_code == 400:
                raise HisNotFound("patient_not_found")
            if response.status_code >= 500:
                last_error = HisUnavailable("his_unavailable")
                continue
            if response.status_code != 200:
                last_error = HisUnavailable("his_unavailable")
                continue

            payload = response.json()
            if not payload.get("success") or not payload.get("data"):
                raise HisNotFound("patient_not_found")

            patient = payload["data"][0]
            patient_id = patient.get("mpersonid")
            if not patient_id:
                raise HisUnavailable("his_invalid_response")

            return HisPatient(
                patient_id=str(patient_id),
                name=patient.get("mname"),
                birth_date=_convert_roc_date(patient.get("mbirthdt")),
                sex=_convert_sex(patient.get("msex")),
            )

        raise HisUnavailable("his_unavailable") from last_error
