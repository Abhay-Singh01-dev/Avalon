from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.core.external_cache import external_cache

logger = logging.getLogger(__name__)


class ClinicalTrialsClient:
    def __init__(self):
        self.base_url = settings.CLINICALTRIALS_BASE_URL
        self.timeout = settings.EXTERNAL_REQUEST_TIMEOUT
        self.max_records = settings.CLINICALTRIALS_MAX_RECORDS
        self.cache_ttl = settings.CLINICALTRIALS_CACHE_TTL
        self.max_retries = settings.EXTERNAL_MAX_RETRIES
        self.headers = {"User-Agent": "PharmaAI/1.0"}

    async def search(
        self,
        condition: Optional[str] = None,
        intervention: Optional[str] = None,
        disease: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        expr = self._build_expression(condition, intervention, disease)
        if not expr:
            return []
        params = {
            "expr": expr,
            "min_rnk": 1,
            "max_rnk": min(max_results or self.max_records, self.max_records),
            "fmt": "json",
            "fields": ",".join(
                [
                    "NCTId",
                    "BriefTitle",
                    "Condition",
                    "Phase",
                    "OverallStatus",
                    "LeadSponsorName",
                    "LocationCountry",
                    "LocationCity",
                    "LocationFacility",
                    "EnrollmentCount",
                    "ResultsFirstPostDate",
                    "StudyType",
                    "LastUpdatePostDate",
                    "OfficialTitle",
                ]
            ),
        }

        cache_key = {"expr": expr, "max": params["max_rnk"]}
        cached = external_cache.get("clinical_trials", cache_key)
        if cached is not None:
            return cached

        data = await self._request(params)
        studies = data.get("StudyFieldsResponse", {}).get("StudyFields", [])
        parsed = [self._parse_study(study) for study in studies]
        external_cache.set("clinical_trials", cache_key, parsed, ttl=self.cache_ttl)
        return parsed

    async def _request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                    response = await client.get(self.base_url, params=params)
            except httpx.RequestError as exc:
                logger.warning("ClinicalTrials request failed: %s", exc)
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(2 ** attempt)
                continue

            if response.status_code >= 500:
                await asyncio.sleep(min(5, 2 ** attempt))
                continue

            response.raise_for_status()
            return response.json()

        raise RuntimeError("ClinicalTrials request failed after retries")

    def _build_expression(self, condition: Optional[str], intervention: Optional[str], disease: Optional[str]) -> str:
        tokens = [token for token in [condition, intervention, disease] if token]
        return " AND ".join(f'"{token}"' for token in tokens)

    def _parse_study(self, record: Dict[str, Any]) -> Dict[str, Any]:
        def pick(field: str) -> Optional[str]:
            value = record.get(field) or []
            return value[0] if value else None

        nct_id = pick("NCTId")
        return {
            "nct_id": pick("NCTId"),
            "title": pick("BriefTitle") or pick("OfficialTitle"),
            "phase": pick("Phase"),
            "status": pick("OverallStatus"),
            "sponsor": pick("LeadSponsorName"),
            "locations": [
                {
                    "facility": facility,
                    "city": city,
                    "country": country,
                }
                for facility, city, country in zip(
                    record.get("LocationFacility", []),
                    record.get("LocationCity", []),
                    record.get("LocationCountry", []),
                )
            ],
            "enrollment": pick("EnrollmentCount"),
            "results_link": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else None,
            "study_type": pick("StudyType"),
            "last_updated": pick("LastUpdatePostDate"),
        }


clinicaltrials_client = ClinicalTrialsClient()

