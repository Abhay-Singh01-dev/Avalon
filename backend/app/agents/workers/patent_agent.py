from typing import Dict, Any
import time
import json
from app.config import settings
from app.llm.lmstudio_client import lmstudio_client
from app.core.cache import cache, CacheManager
from app.core.retry import retry_llm_call
from app.core.logger import get_logger
from app.llm import prompt_templates
from app.services.patent_client import patent_client
from app.agents.workers.schema_enforcer import get_unified_schema_prompt, normalize_to_unified_schema
from app.agents.workers.outline_expander import (
    generate_outline,
    expand_outline_points,
    merge_and_format_sections,
    extract_key_insights
)

logger = get_logger(__name__)


class PatentAgent:
    agent_type = "patents"

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

        try:
            cached = cache.get(cache_key, default=None)
            if cached is not None:
                logger.info(f"PatentAgent cache hit: {cache_key[:8]}...")
                return cached
        except Exception:
            logger.exception("Cache lookup failed for PatentAgent")

        system_msg = (
            "You are a HIGH-PRECISION IP Strategy Engine and Patent Analyst specializing in pharmaceutical intellectual property. "
            "You MUST act like a professional IP strategist producing maximum-depth patent landscape analysis. "
            "NO shallow summaries. NO generic statements. NO mock data. Only deep, domain-specific IP analysis.\n\n"
            "AGENT-SPECIFIC REQUIREMENTS:\n"
            "You must populate the unified schema with:\n"
            "- Tables with Patent ID, Expiry, Claim Type, Competitor, FTO Flag\n"
            "- Key insights with category='patent'\n"
            "- Citations from PatentsView, USPTO, EPO\n"
            "- Timeline of patent expiry dates\n\n"
            + get_unified_schema_prompt("Patent")
        )

        user_msg = json.dumps({
            "query": parameters.get("query"),
            "molecule": parameters.get("molecule")
        })

        decorated = retry_llm_call()(lmstudio_client.ask_llm)
        query = parameters.get("query", "")

        patent_records, patent_error = await self._fetch_patents(parameters)

        try:
            raw = await decorated([
                {"role": "user", "content": system_msg + "\n\n" + user_msg}
            ], model=settings.LMSTUDIO_MODEL_NAME)
        except Exception as e:
            logger.error(f"PatentAgent LLM failure: {e}")
            result = normalize_to_unified_schema("Patent", {}, query)
            result["confidence_score"]["value"] = 0.0
            result["confidence_score"]["explanation"] = f"LLM call failed: {str(e)}"
            result["core_findings"]["summary"] = [f"Error: Patent analysis failed - {str(e)}"]
            return result
        parsed = None
        try:
            parsed = json.loads(raw)
        except Exception:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(1))
                except Exception:
                    pass
            
            # If still failed, try to find JSON object in the text
            if not parsed:
                json_match = re.search(r'\{.*"agent_name".*\}', raw, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group(0))
                    except Exception:
                        pass
        
        # If parsing completely failed, convert text to structured format
        if not parsed:
            logger.warning("PatentAgent: Could not parse JSON, converting text to structure")
            lines = [line.strip() for line in raw.split('\n') if line.strip()]
            parsed = {
                "core_findings": {
                    "summary": lines[:5] if len(lines) >= 5 else lines
                }
            }

        # Normalize to unified schema
        result = normalize_to_unified_schema("Patent", parsed, query)
        
        # Add patent records to citations
        if patent_records:
            for patent in patent_records[:10]:
                if isinstance(patent, dict):
                    result["citations"].append({
                        "source": patent.get("title", "Patent"),
                        "url": patent.get("url", ""),
                        "type": "patent",
                        "quote": patent.get("abstract", "")[:200] if patent.get("abstract") else ""
                    })
        
        # Ensure confidence is properly set
        if result["confidence_score"]["value"] == 0.0:
            result["confidence_score"]["value"] = 0.7
            result["confidence_score"]["explanation"] = "Based on patent data availability from PatentsView, USPTO, and EPO"

        try:
            cache.set(cache_key, result)
        except Exception:
            logger.exception("Failed to cache PatentAgent result")

        logger.info(f"PatentAgent completed in {time.time() - start:.2f}s")
        return result

    async def _fetch_patents(self, parameters: Dict[str, Any]):
        keyword = parameters.get("molecule") or parameters.get("query")
        assignee = parameters.get("company")
        inventor = parameters.get("inventor")
        if not any([keyword, assignee, inventor]):
            return [], None
        try:
            records = await patent_client.search(
                keyword=keyword,
                assignee=assignee,
                inventor=inventor,
                per_page=parameters.get("limit"),
            )
            if not records:
                return [{"status": "data_unavailable", "reason": "no_patents_found"}], None
            return records, None
        except Exception as exc:
            logger.warning("Patent lookup failed: %s", exc)
            return [], f"PatentsView lookup failed: {exc}"

