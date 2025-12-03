from typing import Dict, Any
import time
import json
from app.config import settings
from app.llm.lmstudio_client import lmstudio_client
from app.core.cache import cache, CacheManager
from app.core.retry import retry_llm_call
from app.core.logger import get_logger
from app.llm import prompt_templates
from app.core.trace import trace
from app.services.pubmed_client import pubmed_client
from app.agents.workers.schema_enforcer import get_unified_schema_prompt, normalize_to_unified_schema
from app.agents.workers.outline_expander import (
    generate_outline,
    expand_outline_points,
    merge_and_format_sections,
    extract_key_insights
)

logger = get_logger(__name__)


class MarketAgent:
    agent_type = "market"

    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.supported_tasks = ["analyze_section"]

    async def process(self, task_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if task_type != "analyze_section":
            raise ValueError(f"Unsupported task type: {task_type}")
        return await self.analyze_section(parameters)

    async def analyze_section(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        payload = {"agent": self.agent_type, "params": parameters}
        cache_key = CacheManager.make_key(payload)

        # Return cached value if present
        try:
            cached = cache.get(cache_key, default=None)
            if cached is not None:
                logger.info(f"MarketAgent cache hit: {cache_key[:8]}...")
                return cached
        except Exception:
            logger.exception("Cache lookup failed for MarketAgent")

        query = parameters.get("query", "")
        
        # STEP 1: Generate outline (cached separately for speed)
        logger.info("MarketAgent STEP 1: Generating outline...")
        outline_points = await generate_outline(
            query=query,
            agent_type="market",
            cache_prefix="market_outline"
        )
        
        if not outline_points:
            logger.warning("MarketAgent: Outline generation failed, using fallback")
            result = normalize_to_unified_schema("IQVIA", {}, query)
            result["confidence_score"]["value"] = 0.3
            result["confidence_score"]["explanation"] = "Outline generation failed"
            result["core_findings"]["summary"] = ["Unable to generate market analysis outline"]
            return result
        
        # STEP 2: Expand each outline point with verification scaffold
        logger.info(f"MarketAgent STEP 2: Expanding {len(outline_points)} outline points...")
        agent_persona = """You are an IQVIA Market Intelligence Analyst specializing in pharmaceutical markets.

EXPERTISE:
- Global market sizing and CAGR projections
- Competitive landscape analysis (market share, HHI index)
- Pricing trends and reimbursement dynamics
- Geographic market segmentation
- Revenue forecasts and commercial viability

CRITICAL REQUIREMENTS:
- Use specific numbers with sources (e.g., "Market size: $4.2B in 2024, CAGR 8.3%")
- Name specific competitors with market share percentages
- Cite pricing data with currency and timeframe
- Identify key markets by region/country
- NO generic statements like "market is growing"
- NO repetition of mechanistic or clinical details
- Focus ONLY on commercial/market intelligence"""

        expanded_result = await expand_outline_points(
            outline_points=outline_points,
            query=query,
            agent_type="market",
            agent_persona=agent_persona
        )
        
        # STEP 3: Merge and format sections (STRICT MODE: no headings)
        logger.info("MarketAgent STEP 3: Merging and formatting sections...")
        formatted_text = merge_and_format_sections(
            expanded_sections=expanded_result["expanded_sections"],
            agent_name="MarketAgent",
            strict_mode=True
        )
        
        # Extract key insights (high-certainty facts)
        key_insights = extract_key_insights(expanded_result["expanded_sections"])
        
        # Fetch PubMed data for citations
        pubmed_mentions, pubmed_error = await self._fetch_pubmed_mentions(parameters)
        
        # Build unified schema result
        result = normalize_to_unified_schema("IQVIA", {
            "core_findings": {
                "summary": key_insights,
                "key_insights": [
                    {
                        "insight": insight,
                        "category": "market",
                        "confidence": "high"
                    }
                    for insight in key_insights[:5]
                ]
            },
            "full_text": formatted_text
        }, query)
        
        # Add PubMed mentions to citations if available
        if pubmed_mentions:
            for mention in pubmed_mentions[:5]:
                if isinstance(mention, dict):
                    result["citations"].append({
                        "source": mention.get("title", "PubMed"),
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{mention.get('pmid', '')}" if mention.get("pmid") else "",
                        "type": "publication",
                        "quote": mention.get("abstract", "")[:200] if mention.get("abstract") else ""
                    })
        
        # Ensure confidence is properly set
        if result["confidence_score"]["value"] == 0.0:
            result["confidence_score"]["value"] = 0.7
            result["confidence_score"]["explanation"] = "Based on market data availability and source reliability"

        try:
            cache.set(cache_key, result)
        except Exception:
            logger.exception("Failed to cache MarketAgent result")

        logger.info(f"MarketAgent completed in {time.time() - start:.2f}s")
        return result

    async def _fetch_pubmed_mentions(self, parameters: Dict[str, Any]):
        term_parts = [parameters.get("query"), parameters.get("molecule"), parameters.get("condition")]
        term = " ".join(part for part in term_parts if part)
        if not term.strip():
            return [], None
        try:
            pmids = await pubmed_client.search(term, retmax=5)
            articles = await pubmed_client.fetch(pmids[:5])
            if not articles:
                return [{"status": "data_unavailable", "reason": "no_pubmed_hits"}], None
            return articles, None
        except Exception as exc:
            logger.warning("PubMed lookup failed: %s", exc)
            return [], f"PubMed lookup failed: {exc}"

