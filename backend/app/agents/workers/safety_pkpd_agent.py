from typing import Dict, Any
import time
import json
from app.config import settings
from app.llm.lmstudio_client import lmstudio_client
from app.core.cache import cache, CacheManager
from app.core.retry import retry_llm_call
from app.core.logger import get_logger
from app.agents.workers.outline_expander import (
    generate_outline,
    expand_outline_points,
    merge_and_format_sections,
    extract_key_insights
)

logger = get_logger(__name__)


class SafetyPKPDAgent:
    agent_type = "safety"

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
                logger.info(f"SafetyPKPDAgent cache hit: {cache_key[:8]}...")
                return cached
        except Exception:
            logger.exception("Cache lookup failed for SafetyPKPDAgent")

        query = parameters.get("query", "")
        
        # STEP 1: Generate outline
        logger.info("SafetyPKPDAgent STEP 1: Generating outline...")
        outline_points = await generate_outline(
            query=query,
            agent_type="safety",
            cache_prefix="safety_outline"
        )
        
        if not outline_points:
            return {
                "agent_name": "SafetyPKPDAgent",
                "summary": ["Unable to generate safety/PKPD outline"],
                "confidence_score": 0.3
            }
        
        # STEP 2: Expand with verification scaffold
        logger.info(f"SafetyPKPDAgent STEP 2: Expanding {len(outline_points)} points...")
        agent_persona = """You are a Safety & PK/PD Analyst specializing in pharmaceutical mechanism and pharmacology.

EXPERTISE:
- Mechanism of Action (MoA): molecular targets, binding affinity, receptor interactions
- Pharmacokinetics (PK): half-life, clearance, bioavailability, Vd, Cmax, Tmax, AUC
- Pharmacodynamics (PD): EC50/IC50 values, dose-response, therapeutic window
- Safety Profile: adverse events, organ toxicity, DDI risks, contraindications
- Toxicology: therapeutic index, dose adjustments (renal/hepatic), black box warnings

CRITICAL REQUIREMENTS:
- Use specific PK parameters with units (e.g., "t1/2 = 6.5 hours, Vd = 0.7 L/kg")
- Name molecular targets precisely (e.g., "5-HT2A receptor antagonist, Ki = 2.1 nM")
- Cite specific adverse events with incidence rates
- Include dose ranges and administration routes
- NO generic statements like "drug is well-tolerated"
- NO repetition of market or trial details
- Focus ONLY on mechanism, PK/PD, and safety"""

        expanded_result = await expand_outline_points(
            outline_points=outline_points,
            query=query,
            agent_type="safety",
            agent_persona=agent_persona
        )
        
        # STEP 3: Merge and format
        logger.info("SafetyPKPDAgent STEP 3: Merging sections...")
        formatted_text = merge_and_format_sections(
            expanded_sections=expanded_result["expanded_sections"],
            agent_name="SafetyPKPDAgent",
            strict_mode=True
        )
        
        key_insights = extract_key_insights(expanded_result["expanded_sections"])
        
        result = {
            "agent_name": "SafetyPKPDAgent",
            "summary": key_insights,
            "full_text": formatted_text,
            "confidence_score": 0.85,
            "provenance": ["safety"]
        }

        system_msg_old = (
            "You are a HIGH-PRECISION Safety & PK/PD Analyst specializing in pharmaceutical mechanism of action, "
            "pharmacokinetics, and safety analysis. You MUST produce maximum-depth, evidence-driven analysis. "
            "NO shallow summaries. NO generic statements. NO mock data. Only deep, domain-specific analysis.\n\n"
            "MANDATORY ANALYSIS REQUIREMENTS:\n\n"
            "A. Mechanism of Action (MoA) Deep Dive:\n"
            "- Mechanistic pathway overview (detailed)\n"
            "- Target class + drug category\n"
            "- Known on-target effects (detailed)\n"
            "- Known off-target effects (detailed)\n"
            "- Binding affinity (if available)\n"
            "- Selectivity profile\n\n"
            "B. Pharmacokinetics (PK) Profile:\n"
            "- Half-life (t1/2) with elimination route\n"
            "- Bioavailability (F%) and route of administration\n"
            "- Volume of distribution (Vd)\n"
            "- Clearance (CL) and organ responsible\n"
            "- Cmax, Tmax, AUC values (if available)\n"
            "- BBB penetration (if CNS indication)\n\n"
            "C. Pharmacodynamics (PD) Profile:\n"
            "- EC50 / IC50 values\n"
            "- Therapeutic window\n"
            "- Dose-response relationship\n"
            "- Time to effect\n"
            "- Duration of effect\n\n"
            "D. Safety & Toxicology:\n"
            "- Organ toxicity signals (by organ system)\n"
            "- Therapeutic index (TI)\n"
            "- Major DDI risks (with specific drugs)\n"
            "- Dose adjustments in renal impairment (detailed)\n"
            "- Dose adjustments in hepatic impairment (detailed)\n"
            "- Contraindications\n"
            "- Black box warnings (if applicable)\n\n"
            "OUTPUT FORMAT (JSON):\n"
            "{\n"
            '  "summary": "Executive summary (2-3 sentences)",\n'
            '  "details": {\n'
            '    "mechanism_of_action": {\n'
            '      "pathway_overview": "...",\n'
            '      "target_class": "...",\n'
            '      "drug_category": "...",\n'
            '      "on_target_effects": ["..."],\n'
            '      "off_target_effects": ["..."],\n'
            '      "binding_affinity": "...",\n'
            '      "selectivity_profile": "..."\n'
            '    },\n'
            '    "pharmacokinetics": {\n'
            '      "half_life": "...",\n'
            '      "elimination_route": "...",\n'
            '      "bioavailability_pct": "...",\n'
            '      "route_of_administration": "...",\n'
            '      "volume_of_distribution": "...",\n'
            '      "clearance": "...",\n'
            '      "organ_responsible": "...",\n'
            '      "cmax": "...",\n'
            '      "tmax": "...",\n'
            '      "auc": "...",\n'
            '      "bbb_penetration": "yes/no/partial with details"\n'
            '    },\n'
            '    "pharmacodynamics": {\n'
            '      "ec50_ic50": "...",\n'
            '      "therapeutic_window": "...",\n'
            '      "dose_response": "...",\n'
            '      "time_to_effect": "...",\n'
            '      "duration_of_effect": "..."\n'
            '    },\n'
            '    "safety_toxicology": {\n'
            '      "organ_toxicity": [{"organ": "...", "signal": "...", "severity": "..."}],\n'
            '      "therapeutic_index": "...",\n'
            '      "ddi_risks": [{"drug": "...", "interaction": "...", "severity": "..."}],\n'
            '      "renal_impairment_dosing": "...",\n'
            '      "hepatic_impairment_dosing": "...",\n'
            '      "contraindications": ["..."],\n'
            '      "black_box_warnings": ["..."]\n'
            '    }\n'
            '  },\n'
            '  "confidence": 0-100,\n'
            '  "sources": ["PubMed", "FDA label", ...]\n'
            "}\n\n"
            "CRITICAL: Include actual numbers (half-lives, doses, concentrations) whenever possible. "
            "Explain WHY each PK/PD parameter matters clinically. Avoid generic statements. "
            "Provide actionable dosing guidance."
        )

        user_msg = json.dumps({"query": parameters.get("query"), "molecule": parameters.get("molecule")})

        decorated = retry_llm_call()(lmstudio_client.ask_llm)

        try:
            raw = await decorated([
                {"role": "user", "content": system_msg + "\n\n" + user_msg}
            ], model=settings.LMSTUDIO_MODEL_NAME)
        except Exception as e:
            logger.error(f"SafetyPKPDAgent LLM failure: {e}")
            return {"error": "llm_failure", "message": str(e)}

        try:
            parsed = json.loads(raw)
        except Exception:
            logger.error("SafetyPKPDAgent parse failure")
            result = {"error": "parse_failure", "raw": raw}
            try:
                cache.set(cache_key, result)
            except Exception:
                logger.exception("Failed to cache parse_failure for SafetyPKPDAgent")
            return result

        summary = parsed.get("summary") or "Safety/PKPD overview"
        details = parsed.get("details", parsed)
        confidence = int(parsed.get("confidence", 60)) if isinstance(parsed.get("confidence", 60), (int, float)) else 60
        confidence = max(0, min(100, confidence))

        result = {
            "section": "safety",
            "summary": summary,
            "details": details,
            "confidence": confidence,
            "raw": raw,
            "cache_key": cache_key
        }

        try:
            cache.set(cache_key, result)
        except Exception:
            logger.exception("Failed to cache SafetyPKPDAgent result")

        logger.info(f"SafetyPKPDAgent completed in {time.time() - start:.2f}s")
        return result
