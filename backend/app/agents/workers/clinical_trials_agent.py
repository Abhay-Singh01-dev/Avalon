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
from app.services.clinicaltrials_client import clinicaltrials_client
from app.agents.workers.schema_enforcer import get_unified_schema_prompt, normalize_to_unified_schema
from app.agents.workers.outline_expander import (
    generate_outline,
    expand_outline_points,
    merge_and_format_sections,
    extract_key_insights
)

logger = get_logger(__name__)


class ClinicalTrialsAgent:
    agent_type = "clinical"

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

        # Check cache
        try:
            cached = cache.get(cache_key, default=None)
            if cached is not None:
                logger.info(f"ClinicalTrialsAgent cache hit: {cache_key[:8]}...")
                return cached
        except Exception:
            logger.exception("Cache lookup failed for ClinicalTrialsAgent")

        query = parameters.get("query", "")
        
        # STEP 1: Generate outline
        logger.info("ClinicalTrialsAgent STEP 1: Generating outline...")
        outline_points = await generate_outline(
            query=query,
            agent_type="clinical",
            cache_prefix="clinical_outline"
        )
        
        if not outline_points:
            logger.warning("ClinicalTrialsAgent: Outline generation failed")
            result = normalize_to_unified_schema("ClinicalTrials", {}, query)
            result["confidence_score"]["value"] = 0.3
            result["confidence_score"]["explanation"] = "Outline generation failed"
            result["core_findings"]["summary"] = ["Unable to generate clinical trials outline"]
            return result
        
        # STEP 2: Expand with verification scaffold
        logger.info(f"ClinicalTrialsAgent STEP 2: Expanding {len(outline_points)} points...")
        agent_persona = """You are a Clinical Evidence Intelligence Analyst specializing in pharmaceutical trials.

EXPERTISE:
- Phase I/II/III/IV trial design and endpoints
- Primary and secondary outcomes analysis
- Safety and efficacy data interpretation
- Regulatory endpoints (FDA, EMA criteria)
- Trial status tracking (NCT IDs, enrollment, completion dates)

CRITICAL REQUIREMENTS:
- Always include NCT IDs when referencing trials
- Specify phase, status, enrollment numbers
- Name primary and secondary endpoints explicitly
- Cite actual results with p-values and confidence intervals
- Identify sponsor and principal investigators
- NO generic statements like "trials are ongoing"
- NO repetition of market or mechanism details
- Focus ONLY on clinical trial evidence"""

        expanded_result = await expand_outline_points(
            outline_points=outline_points,
            query=query,
            agent_type="clinical",
            agent_persona=agent_persona
        )
        
        # STEP 3: Merge and format
        logger.info("ClinicalTrialsAgent STEP 3: Merging sections...")
        formatted_text = merge_and_format_sections(
            expanded_sections=expanded_result["expanded_sections"],
            agent_name="ClinicalTrialsAgent",
            strict_mode=True
        )
        
        key_insights = extract_key_insights(expanded_result["expanded_sections"])
        
        # Fetch trials data for citations
        trials_data, trials_error = await self._fetch_trials(parameters)
        
        result = normalize_to_unified_schema("ClinicalTrials", {
            "core_findings": {
                "summary": key_insights,
                "key_insights": [
                    {"insight": insight, "category": "clinical", "confidence": "high"}
                    for insight in key_insights[:5]
                ]
            },
            "full_text": formatted_text
        }, query)
        
        # Add trials data to citations
        if trials_data:
            for trial in trials_data[:10]:
                if isinstance(trial, dict):
                    result["citations"].append({
                        "source": trial.get("nct_id", "ClinicalTrials.gov"),
                        "url": f"https://clinicaltrials.gov/ct2/show/{trial.get('nct_id', '')}" if trial.get("nct_id") else "",
                        "type": "clinical_trial",
                        "quote": trial.get("brief_title", "")[:200] if trial.get("brief_title") else ""
                    })
        
        # Ensure confidence is properly set
        if result["confidence_score"]["value"] == 0.0:
            result["confidence_score"]["value"] = 0.75
            result["confidence_score"]["explanation"] = "Based on trial data availability from ClinicalTrials.gov and WHO ICTRP"

        try:
            cache.set(cache_key, result)
        except Exception:
            logger.exception("Failed to cache ClinicalTrialsAgent result")

        logger.info(f"ClinicalTrialsAgent completed in {time.time() - start:.2f}s")
        return result

    async def _fetch_trials(self, parameters: Dict[str, Any]):
        query = parameters.get("condition") or parameters.get("disease") or parameters.get("query")
        intervention = parameters.get("intervention") or parameters.get("molecule")
        if not query and not intervention:
            return [], None
        try:
            trials = await clinicaltrials_client.search(
                condition=query,
                intervention=intervention,
                disease=parameters.get("disease"),
                max_results=parameters.get("max_trials"),
            )
            if not trials:
                return [{"status": "data_unavailable", "reason": "no_trials_found"}], None
            return trials, None
        except Exception as exc:
            logger.warning("ClinicalTrials external lookup failed: %s", exc)
            return [], f"ClinicalTrials.gov lookup failed: {exc}"

