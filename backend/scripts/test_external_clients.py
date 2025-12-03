import asyncio
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.pubmed_client import pubmed_client  # noqa: E402
from app.services.clinicaltrials_client import clinicaltrials_client  # noqa: E402
from app.services.patent_client import patent_client  # noqa: E402


async def run_tests():
    results = {}

    pmids = await pubmed_client.search("metformin Parkinson's", retmax=3)
    articles = await pubmed_client.fetch(pmids[:1])
    results["pubmed"] = {"pmids": pmids, "sample": articles[:1]}

    trials = await clinicaltrials_client.search(condition="parkinson disease", intervention="levodopa")
    results["clinical_trials"] = trials[:2]

    patents = await patent_client.search(keyword="minocycline")
    results["patents"] = patents[:2]

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(run_tests())

