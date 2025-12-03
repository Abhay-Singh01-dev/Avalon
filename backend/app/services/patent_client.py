from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.core.external_cache import external_cache

logger = logging.getLogger(__name__)


class PatentClient:
    def __init__(self):
        self.base_url = settings.PATENTSVIEW_BASE_URL
        self.timeout = settings.EXTERNAL_REQUEST_TIMEOUT
        self.page_size = settings.PATENTSVIEW_PAGE_SIZE
        self.cache_ttl = settings.PATENTSVIEW_CACHE_TTL
        self.max_retries = settings.EXTERNAL_MAX_RETRIES

    async def search(
        self,
        keyword: Optional[str] = None,
        assignee: Optional[str] = None,
        inventor: Optional[str] = None,
        per_page: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        query = self._build_query(keyword, assignee, inventor)
        if not query:
            return []

        options = {"per_page": min(per_page or self.page_size, self.page_size)}
        params = {
            "q": json.dumps(query),
            "f": json.dumps(
                [
                    "patent_number",
                    "patent_title",
                    "patent_date",
                    "patent_abstract",
                    "patent_application_date",
                    "patent_type",
                    "cpc_subgroup_id",
                    "inventor_last_name",
                    "inventor_first_name",
                    "assignee_organization",
                    "assignee_type",
                ]
            ),
            "o": json.dumps(options),
        }

        cache_key = {"query": query, "options": options}
        cached = external_cache.get("patents", cache_key)
        if cached is not None:
            return cached

        payload = await self._request(params)
        patents = payload.get("patents", [])
        parsed = [self._parse_patent(record) for record in patents]
        external_cache.set("patents", cache_key, parsed, ttl=self.cache_ttl)
        return parsed

    async def _request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"User-Agent": "PharmaAI/1.0"}
        if settings.PATENTSVIEW_API_KEY:
            headers["x-api-key"] = settings.PATENTSVIEW_API_KEY

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
                    response = await client.get(self.base_url, params=params)
            except httpx.RequestError as exc:
                logger.warning("PatentsView request failed: %s", exc)
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(2 ** attempt)
                continue

            if response.status_code >= 500:
                await asyncio.sleep(min(5, 2 ** attempt))
                continue

            response.raise_for_status()
            return response.json()

        raise RuntimeError("PatentsView request failed after retries")

    def _build_query(
        self, keyword: Optional[str], assignee: Optional[str], inventor: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        filters = []
        if keyword:
            filters.append({"_text_any": {"patent_title": keyword}})
        if assignee:
            filters.append({"_text_any": {"assignee_organization": assignee}})
        if inventor:
            filters.append({"_text_any": {"inventor_full_name": inventor}})
        if not filters:
            return None
        if len(filters) == 1:
            return filters[0]
        return {"_and": filters}

    def _parse_patent(self, record: Dict[str, Any]) -> Dict[str, Any]:
        inventors = self._extract_people(record)
        assignees = self._extract_assignees(record)
        grant_date = record.get("patent_date")
        application_date = record.get("patent_application_date")
        expired = self._is_expired(grant_date, application_date)

        return {
            "patent_number": record.get("patent_number"),
            "title": record.get("patent_title"),
            "abstract": record.get("patent_abstract"),
            "grant_date": grant_date,
            "application_date": application_date,
            "inventors": inventors,
            "assignees": assignees,
            "expired": expired,
            "url": f"https://patents.google.com/patent/{record.get('patent_number')}" if record.get("patent_number") else None,
            "type": record.get("patent_type"),
        }

    def _is_expired(self, grant_date: Optional[str], application_date: Optional[str]) -> Optional[bool]:
        reference_date = application_date or grant_date
        if not reference_date:
            return None
        try:
            base = datetime.strptime(reference_date, "%Y-%m-%d")
        except ValueError:
            return None
        expiry = base + timedelta(days=365 * 20)
        return datetime.utcnow() > expiry

    def _extract_people(self, record: Dict[str, Any]) -> List[str]:
        people: List[str] = []
        if record.get("inventors"):
            for inventor in record["inventors"]:
                full_name = " ".join(
                    part
                    for part in [
                        inventor.get("inventor_first_name"),
                        inventor.get("inventor_last_name"),
                    ]
                    if part
                )
                if full_name:
                    people.append(full_name)
        else:
            firsts = record.get("inventor_first_name", [])
            lasts = record.get("inventor_last_name", [])
            for first, last in zip(firsts, lasts):
                name = " ".join(part for part in [first, last] if part)
                if name:
                    people.append(name)
        return people

    def _extract_assignees(self, record: Dict[str, Any]) -> List[str]:
        if record.get("assignees"):
            return [
                assignee.get("assignee_organization")
                for assignee in record["assignees"]
                if assignee.get("assignee_organization")
            ]
        orgs = record.get("assignee_organization", [])
        if isinstance(orgs, str):
            orgs = [orgs]
        return [org for org in orgs if org]


patent_client = PatentClient()

