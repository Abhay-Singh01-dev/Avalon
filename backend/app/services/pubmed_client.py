from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

import httpx

from app.config import settings
from app.core.external_cache import external_cache

logger = logging.getLogger(__name__)


@dataclass
class AsyncRateLimiter:
    max_calls: int
    period: float

    def __post_init__(self):
        self._lock = asyncio.Lock()
        self._calls: List[float] = []

    async def acquire(self):
        while True:
            async with self._lock:
                now = asyncio.get_event_loop().time()
                self._calls = [ts for ts in self._calls if now - ts < self.period]
                if len(self._calls) < self.max_calls:
                    self._calls.append(now)
                    return
                wait_time = self.period - (now - self._calls[0])
            await asyncio.sleep(max(0.05, wait_time))


class PubMedClient:
    def __init__(self):
        self.base_url = settings.PUBMED_BASE_URL.rstrip("/")
        self.timeout = settings.EXTERNAL_REQUEST_TIMEOUT
        self.max_retries = settings.EXTERNAL_MAX_RETRIES
        self.rate_limiter = AsyncRateLimiter(max(1, int(settings.PUBMED_RATE_LIMIT_RPS)), 1.0)
        self.headers = {"User-Agent": "PharmaAI/1.0 (contact: support@pharma.ai)"}

    async def search(self, term: str, retmax: int = 20) -> List[str]:
        if not term:
            return []
        identifier = {"term": term, "retmax": retmax}
        cached = external_cache.get("pubmed_search", identifier)
        if cached is not None:
            return cached

        params = {
            "db": "pubmed",
            "term": term,
            "retmax": retmax,
            "retmode": "json",
            "sort": "most+recent",
        }
        data = await self._request("esearch.fcgi", params)
        pmids = data.get("esearchresult", {}).get("idlist", [])
        external_cache.set("pubmed_search", identifier, pmids, ttl=60 * 60 * 6)
        return pmids

    async def fetch(self, pmids: List[str]) -> List[Dict[str, Any]]:
        pmids = [p for p in pmids if p]
        if not pmids:
            return []
        identifier = {"pmids": pmids}
        cached = external_cache.get("pubmed_fetch", identifier)
        if cached is not None:
            return cached

        params = {
            "db": "pubmed",
            "retmode": "xml",
            "id": ",".join(pmids[:200]),
        }
        xml_text = await self._request("efetch.fcgi", params, expect_json=False)
        try:
            parsed = self._parse_pubmed_xml(xml_text)
        except Exception as exc:  # pragma: no cover - defensive parsing
            logger.warning("Failed to parse PubMed XML: %s", exc)
            parsed = []
        external_cache.set("pubmed_fetch", identifier, parsed, ttl=60 * 60 * 24)
        return parsed

    async def _request(self, endpoint: str, params: Dict[str, Any], expect_json: bool = True) -> Any:
        url = f"{self.base_url}/{endpoint}"
        for attempt in range(1, self.max_retries + 1):
            await self.rate_limiter.acquire()
            try:
                async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                    response = await client.get(url, params=params)
            except httpx.RequestError as exc:
                logger.warning("PubMed request error: %s", exc)
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(2 ** attempt)
                continue

            if response.status_code == 429:
                await asyncio.sleep(min(5, 2 ** attempt))
                continue
            if response.status_code >= 500:
                await asyncio.sleep(min(5, 2 ** attempt))
                continue

            response.raise_for_status()
            return response.json() if expect_json else response.text

        raise RuntimeError("PubMed request failed after retries")

    def _parse_pubmed_xml(self, xml_text: str) -> List[Dict[str, Any]]:
        root = ET.fromstring(xml_text)
        articles = []
        for article in root.findall(".//PubmedArticle"):
            pmid = article.findtext(".//MedlineCitation/PMID")
            title = (article.findtext(".//ArticleTitle") or "").strip()
            abstract_nodes = article.findall(".//Abstract/AbstractText")
            abstract = " ".join(node.text or "" for node in abstract_nodes).strip()
            journal = (article.findtext(".//Journal/Title") or "").strip()
            year = (
                article.findtext(".//ArticleDate/Year")
                or article.findtext(".//PubDate/Year")
                or article.findtext(".//Article/Journal/JournalIssue/PubDate/Year")
            )
            try:
                year = int(year) if year else None
            except ValueError:
                year = None

            authors = []
            for author in article.findall(".//AuthorList/Author"):
                last = author.findtext("LastName") or ""
                fore = author.findtext("ForeName") or author.findtext("Initials") or ""
                full_name = " ".join(part for part in [fore.strip(), last.strip()] if part)
                if full_name:
                    authors.append(full_name)

            articles.append(
                {
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract,
                    "journal": journal,
                    "authors": authors,
                    "year": year,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                }
            )
        return articles


pubmed_client = PubMedClient()

