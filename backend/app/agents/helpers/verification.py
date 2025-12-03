"""Helpers to verify sources and propose concrete checks for claims."""
from typing import List, Dict, Any
from urllib.parse import urlparse

AUTHORITATIVE_DOMAINS = [
    "pubmed.ncbi.nlm.nih.gov",
    "www.ncbi.nlm.nih.gov",
    "clinicaltrials.gov",
    "patents.google.com",
    "patentimages.storage.googleapis.com",
    "europepmc.org",
]


def domain_authority(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        for d in AUTHORITATIVE_DOMAINS:
            if d in host:
                return "high"
        if host.endswith(".gov") or host.endswith(".edu"):
            return "high"
        return "low"
    except Exception:
        return "unknown"


def verify_sources(sources: List[str]) -> List[Dict[str, Any]]:
    results = []
    for s in sources:
        res = {"source": s, "authority": domain_authority(s)}
        results.append(res)
    return results


def propose_checks_for_claim(claim: str) -> List[str]:
    # Simple heuristic suggestions; LLM verification adds more later
    checks = []
    if len(claim) < 200:
        checks.append(f"PubMed search: {claim}")
        checks.append(f"ClinicalTrials.gov search: {claim}")
    else:
        checks.append(f"PubMed search: {claim.split('.')[:1]}")
    return checks
