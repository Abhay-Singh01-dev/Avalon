"""
Avalon Auto-Mode Intelligence - Automatic Structure Detection

This module provides fully automatic mode detection and agent selection.
User does NOT need to specify "table mode" or "research mode" - the system decides automatically.

AUTO-MODE ENGINE:
1. SIMPLE MODE - Normal/high-level questions (3-6 bullets, no tables)
2. RESEARCH MODE - Disease/drugs/competitors/pathways (structured sections + small tables)
3. TABLE MODE - Comparison queries (automatically detect "compare", "vs", "differences")
4. DOCUMENT MODE - PDF/CSV uploaded
5. SAFETY MODE - Patient-risk/dosing/interactions
6. EXPERT MODE - Expert network/collaboration queries

AUTOMATIC TRIGGERS:
- Compare queries → TABLE MODE (auto-detect comparison intent)
- Market/landscape → RESEARCH MODE (multi-agent routing)
- Simple questions → SIMPLE MODE (3-6 bullets)
- Expert/specialist → EXPERT MODE (graph + top experts)
- Patient/dosing → SAFETY MODE (disclaimer required)
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ChatMode(str, Enum):
    """Auto-mode constants - system decides automatically"""
    PATIENT = "patient"          # Patient-specific with PHI
    RESEARCH = "research"        # Deep pharma research with agents
    DOCUMENT = "document"        # PDF/document analysis
    TABLE = "table"              # Comparison/table generation (auto-detected)
    SAFETY = "safety"            # Non-pharma or risk queries
    SIMPLE = "simple"            # Quick Q&A (3-6 bullets)
    EXPERT = "expert"            # Expert network queries


class ModeClassification:
    """
    Result of mode classification with required agents and LLM configuration.
    """
    
    def __init__(
        self,
        mode: str,
        required_agents: List[str],
        needs_synthesis: bool,
        needs_cloud: bool,
        reason: str,
        priority: int = 5
    ):
        self.mode = mode
        self.required_agents = required_agents
        self.needs_synthesis = needs_synthesis
        self.needs_cloud = needs_cloud
        self.reason = reason
        self.priority = priority
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "mode": self.mode,
            "required_agents": self.required_agents,
            "needs_synthesis": self.needs_synthesis,
            "needs_cloud": self.needs_cloud,
            "reason": self.reason,
            "priority": self.priority
        }


def detect_research_mode(prompt: str, metadata: Optional[Dict[str, Any]] = None) -> ModeClassification:
    """
    Classify prompt into appropriate mode with agent requirements.
    
    Args:
        prompt: User's query text
        metadata: Optional metadata (e.g., document_id, project_id)
    
    Returns:
        ModeClassification with mode type, required agents, and configuration
    """
    prompt_lower = prompt.lower().strip()
    
    # Check for document_id in metadata
    has_document = metadata and metadata.get("document_id") if metadata else False
    
    # ========================================================================
    # PRIORITY 1: PATIENT MODE
    # ========================================================================
    # Detect patient-specific queries with PHI
    patient_indicators = [
        "my patient",
        "patient name",
        "patient id",
        "medical record",
        "hba1c",
        "blood pressure",
        "lab results",
        "vital signs",
        "dosage for patient",
        "adjust dose",
        "patient history",
        "case study",
        "dosage adjustment",
        "dose adjustment",
        "patient with"
    ]
    
    # Check for patient data patterns
    has_patient_data = any(indicator in prompt_lower for indicator in patient_indicators)
    
    # Check for specific measurements (e.g., "HbA1c 8.9%", "weight 108 kg")
    has_measurements = any(unit in prompt_lower for unit in ["%", "kg", "mg/dl", "mmol/l", "bpm"])
    
    if has_patient_data or (has_measurements and "patient" in prompt_lower):
        return ModeClassification(
            mode=ChatMode.PATIENT,
            required_agents=["SafetyAgent", "PKPDAgent", "InternalDocsAgent"],
            needs_synthesis=False,
            needs_cloud=False,  # Always local for PHI
            reason="Patient-specific query detected - requires PHI protection",
            priority=1
        )
    
    # ========================================================================
    # PRIORITY 2: SAFETY MODE
    # ========================================================================
    # Check if prompt is NOT pharma-related
    pharma_keywords = [
        "drug", "drugs", "disease", "diseases", "clinical trial", "clinical trials",
        "mechanism of action", "moa", "pharmacology", "pk/pd", "biomarker", "biomarkers",
        "repurpos", "patent", "regulatory", "adverse event", "safety", "efficacy", "trial",
        "molecule", "compound", "indication", "therapy", "treatment", "medication",
        "pharmaceutical", "pharma", "medicine", "dosage", "formulation",
        "metformin", "diabetes", "adalimumab", "tocilizumab", "oncology", "cancer",
        "glp-1", "sglt2", "statin", "insulin", "chemotherapy", "immunotherapy",
        "therapeutic", "biosimilar", "pipeline", "fda", "ema",
        # Additional pharma terms
        "aspirin", "ibuprofen", "paracetamol", "antibiotic", "antiviral",
        "side effects", "adverse effects", "contraindications", "interactions",
        "file", "upload", "document", "pdf", "analyze", "summarize",
        # Brand drug names (common GLP-1, SGLT2, etc.)
        "ozempic", "mounjaro", "wegovy", "trulicity", "jardiance", "farxiga",
        "semaglutide", "tirzepatide", "dulaglutide", "empagliflozin",
        "humira", "keytruda", "opdivo", "tecfidera", "enbrel",
        # Drug classes and medical terms
        "ace inhibitor", "ace-inhibitor", "arb", "beta blocker", "beta-blocker",
        "calcium channel blocker", "diuretic", "anticoagulant", "antiplatelet",
        "nsaid", "opioid", "benzodiazepine", "ssri", "snri", "antidepressant",
        "antipsychotic", "anticonvulsant", "corticosteroid", "immunosuppressant",
        "cough", "myopathy", "hepatotoxic", "nephrotoxic", "cardiotoxic",
        "warfarin", "heparin", "metoprolol", "atenolol", "lisinopril", "losartan",
        "amlodipine", "hydrochlorothiazide", "furosemide", "digoxin", "amiodarone",
        "atorvastatin", "simvastatin", "rosuvastatin", "pravastatin",
        "resistance", "bacteria", "antibiotic resistance", "beta-lactam",
        "loading dose", "steady state", "half-life", "volume of distribution",
        "clearance", "bioavailability", "absorption", "metabolism", "excretion",
        # Medical/healthcare terms
        "glucose", "blood sugar", "cholesterol", "triglyceride", "hemoglobin",
        "hba1c", "a1c", "blood pressure", "hypertension", "hypotension",
        "cardiovascular", "cardiac", "pulmonary", "respiratory", "neurological",
        "neurology", "psychiatric", "psychiatry", "dermatology", "dermatological",
        "gastrointestinal", "gi", "hepatic", "renal", "nephrology",
        "endocrine", "hormone", "hormonal", "thyroid", "adrenal",
        "immune", "immunology", "autoimmune", "inflammation", "inflammatory",
        "pathology", "pathological", "diagnosis", "diagnostic", "prognosis",
        "symptom", "symptoms", "syndrome", "disorder", "condition",
        "infection", "bacterial", "viral", "fungal", "pathogen",
        "tumor", "tumour", "malignant", "benign", "metastasis",
        "biopsy", "screening", "prevention", "prophylaxis", "vaccine",
        "epidemiology", "prevalence", "incidence", "mortality", "morbidity"
    ]
    
    is_pharma = any(keyword in prompt_lower for keyword in pharma_keywords)
    
    if not is_pharma:
        # Additional check for health-related topics
        health_keywords = [
            "health", "medical", "symptom", "doctor", "hospital", "clinic",
            "physician", "nurse", "patient", "diagnosis", "treatment",
            "therapy", "therapeutic", "wellness", "wellbeing", "care",
            "clinical", "medicine", "medicinal", "pharmaceutical", "pharma",
            "biomedical", "biotechnology", "biotech", "healthcare", "health care"
        ]
        is_health = any(keyword in prompt_lower for keyword in health_keywords)
        
        if not is_health:
            return ModeClassification(
                mode=ChatMode.SAFETY,
                required_agents=[],
                needs_synthesis=False,
                needs_cloud=False,
                reason="Non-pharmaceutical query - blocked by safety filter",
                priority=2
            )
    
    # ========================================================================
    # PRIORITY 3: DOCUMENT MODE
    # ========================================================================
    if has_document:
        return ModeClassification(
            mode=ChatMode.DOCUMENT,
            required_agents=["InternalDocsAgent"],
            needs_synthesis=False,
            needs_cloud=False,
            reason="Document ID provided - analyzing uploaded file",
            priority=3
        )
    
    document_keywords = [
        "pdf", "file", "document", "upload", "analyze this file",
        "summarize this", "extract data", "read the document"
    ]
    
    if any(keyword in prompt_lower for keyword in document_keywords):
        return ModeClassification(
            mode=ChatMode.DOCUMENT,
            required_agents=["InternalDocsAgent"],
            needs_synthesis=False,
            needs_cloud=False,
            reason="Document analysis requested",
            priority=3
        )
    
    # ========================================================================
    # PRIORITY 3.5: Check for deep research keywords FIRST
    # ========================================================================
    # If query contains deep analysis keywords, skip TABLE MODE
    deep_research_keywords = [
        "competitive landscape", "landscape analysis",
        "comprehensive", "detailed analysis", "full report", "deep dive",
        "swot", "opportunity", "unmet needs", "synthesis"
    ]
    
    is_deep_research = any(keyword in prompt_lower for keyword in deep_research_keywords)
    
    # ========================================================================
    # PRIORITY 4: TABLE MODE (AUTO-DETECT COMPARISONS)
    # ========================================================================
    # Automatically trigger for comparison queries without user specifying "table"
    table_keywords = [
        "table", "make a table", "create a table", "overview table",
        "compact table", "comparison table", "compare in table",
        "tabular", "columns", "rows", "side by side"
    ]
    
    # Auto-detect comparison intent (NEW: triggers table mode automatically)
    comparison_keywords = [
        "compare", "vs", "versus", "vs.", "difference", "differences",
        "comparison", "contrast", "compared to", "compare with",
        "better than", "worse than", "advantages", "disadvantages",
        "pros and cons", "strengths and weaknesses",
        "x vs y", "a versus b", "which is better",
        "similarities", "distinctions", "differentiate",
        # Market comparison triggers (but not deep analysis)
        "market landscape", "market segmentation", "segment comparison", "class comparison",
        "drug classes", "therapeutic classes", "compare drugs",
        "compare companies", "compare trials", "compare molecules"
    ]
    
    # Check if query is requesting comparison or table
    is_table_request = any(keyword in prompt_lower for keyword in table_keywords)
    is_comparison = any(keyword in prompt_lower for keyword in comparison_keywords)
    
    # Auto-trigger TABLE MODE for comparisons (UNLESS deep research is needed)
    if (is_table_request or is_comparison) and not is_deep_research:
        return ModeClassification(
            mode=ChatMode.TABLE,
            required_agents=[],  # Direct LLM, no agents
            needs_synthesis=False,
            needs_cloud=False,
            reason=f"{'Comparison' if is_comparison else 'Table'} detected - auto-generating compact table",
            priority=4
        )
    
    # ========================================================================
    # PRIORITY 5: EXPERT MODE (Check BEFORE simple mode)
    # ========================================================================
    # Detect expert/collaboration queries before simple mode catches them
    expert_keywords = [
        "expert", "experts", "specialist", "specialists",
        "opinion", "kol", "kols", "key opinion leader",
        "thought leader", "advisory", "advisor", "advisors",
        "collaboration", "collaborate", "collaborator",
        "network", "expert network", "collaboration network",
        "who are the experts", "leading researchers",
        "top scientists", "opinion leaders", "influencers",
        "academic leaders", "industry experts",
        "find specialist", "find experts", "identify experts",
        "top specialist", "top experts"
    ]
    
    is_expert_query = any(keyword in prompt_lower for keyword in expert_keywords)
    
    if is_expert_query:
        return ModeClassification(
            mode=ChatMode.EXPERT,
            required_agents=["ExpertNetworkAgent"],
            needs_synthesis=False,
            needs_cloud=False,
            reason="Expert network query - routing to expert graph with top specialists",
            priority=5
        )
    
    # ========================================================================
    # PRIORITY 6: SIMPLE MODE (Detect single-entity basic queries FIRST)
    # ========================================================================
    # Required research keywords that MUST be present for RESEARCH mode
    required_research_keywords = [
        "market", "landscape", "competitive", "competitive analysis",
        "clinical trials", "phase", "pipeline", "patent", "patents", "ip",
        "mechanism comparison", "pk/pd", "safety profile", 
        "adverse events patterns", "synthesis", "evidence",
        "regulatory", "trend", "forecast", "global analysis",
        "compare", "comparison", "swot", "opportunity", "unmet needs",
        "comprehensive", "detailed analysis", "full report", "deep dive",
        "competitors", "competitor analysis"
    ]
    
    # Check if ANY required research keyword is present
    has_research_keyword = any(keyword in prompt_lower for keyword in required_research_keywords)
    
    # Simple informational patterns
    simple_keywords = [
        "what is", "what are", "define", "explain", "tell me about",
        "list", "brief", "short", "quick", "summary",
        "how does", "how do", "why does", "why do",
        "side effects", "uses of", "used for", "indication",
        "mechanism of action", "moa"
    ]
    
    simple_patterns = [
        prompt_lower.startswith("what is"),
        prompt_lower.startswith("what are"),
        prompt_lower.startswith("list "),
        prompt_lower.startswith("explain "),
        prompt_lower.startswith("define "),
        prompt_lower.startswith("tell me about"),
        prompt_lower.startswith("how does"),
        prompt_lower.startswith("side effects"),
        "in brief" in prompt_lower,
        "short answer" in prompt_lower
    ]
    
    is_simple_pattern = any(keyword in prompt_lower for keyword in simple_keywords) or any(simple_patterns)
    
    # Check for single entity basic query (one drug, no research keywords)
    words = prompt_lower.split()
    is_short_query = len(words) <= 10  # Short queries are usually simple
    
    # Single entity indicators (asking about ONE thing)
    single_entity_patterns = [
        # Question word + single subject
        prompt_lower.startswith("what is "),
        prompt_lower.startswith("what are "),
        prompt_lower.startswith("how does "),
        prompt_lower.startswith("explain "),
        prompt_lower.startswith("define "),
        prompt_lower.startswith("tell me about "),
        # Simple requests
        "side effects of" in prompt_lower and "?" in prompt,
        "uses of" in prompt_lower and "?" in prompt,
        "used for" in prompt_lower,
        "mechanism of action" in prompt_lower and not has_research_keyword,
        "how does" in prompt_lower and "work" in prompt_lower,
    ]
    
    is_single_entity = any(single_entity_patterns) and is_short_query
    
    # FORCE SIMPLE MODE if:
    # 1. Simple pattern detected AND no research keywords, OR
    # 2. Single entity query (asking about one drug/condition), OR  
    # 3. Short query without research keywords
    if (is_simple_pattern and not has_research_keyword) or is_single_entity:
        return ModeClassification(
            mode=ChatMode.SIMPLE,
            required_agents=[],  # Direct LLM, no agents
            needs_synthesis=False,
            needs_cloud=False,
            reason="Simple informational query - no research analysis needed",
            priority=6
        )
    
    # ========================================================================
    # PRIORITY 7: RESEARCH MODE (STRICT - Only for advanced research queries)
    # ========================================================================
    # RESEARCH MODE requires EXPLICIT research intent with specific keywords
    # This should NOT trigger for simple drug questions
    
    # Count how many research indicators are present
    research_indicator_count = sum(1 for keyword in required_research_keywords if keyword in prompt_lower)
    
    # Check for multi-part questions (multiple subqueries)
    has_multiple_parts = (
        prompt.count("?") > 1 or
        prompt.count(" and ") > 2 or
        prompt.count(",") > 2
    )
    
    # STRICT: Research mode only if:
    # 1. Has at least ONE required research keyword, AND
    # 2. Query is sufficiently complex (not a simple question)
    should_use_research = (
        research_indicator_count > 0 and
        not is_single_entity and
        not is_simple_pattern
    ) or has_multiple_parts
    
    # If it doesn't meet RESEARCH criteria, default to SIMPLE
    if not should_use_research:
        return ModeClassification(
            mode=ChatMode.SIMPLE,
            required_agents=[],
            needs_synthesis=False,
            needs_cloud=False,
            reason="General query - using simple mode (no research analysis needed)",
            priority=6
        )
    
    # If we reach here, it's a genuine RESEARCH query
    research_keywords = required_research_keywords
    
    # AUTO-DETECT which agents are needed based on query keywords
    required_agents = []
    
    # Market analysis
    if any(kw in prompt_lower for kw in ["market", "sales", "revenue", "forecast", "growth", "cagr"]):
        required_agents.append("MarketAgent")
    
    # Clinical trials
    if any(kw in prompt_lower for kw in ["clinical trial", "trial", "study", "efficacy", "phase", "endpoint"]):
        required_agents.append("ClinicalTrialsAgent")
    
    # Patents
    if any(kw in prompt_lower for kw in ["patent", "intellectual property", "ip", "exclusivity", "expiry"]):
        required_agents.append("PatentAgent")
    
    # Regulatory & trade
    if any(kw in prompt_lower for kw in ["regulatory", "fda", "ema", "approval", "pathway", "import", "export"]):
        required_agents.append("EXIMAgent")
    
    # PK/PD & mechanism
    if any(kw in prompt_lower for kw in ["mechanism", "moa", "pk/pd", "pharmacology", "kinetics", "safety"]):
        required_agents.append("PKPDAgent")
    
    # Web intelligence
    if any(kw in prompt_lower for kw in ["news", "recent", "latest", "current", "update", "publication"]):
        required_agents.append("WebIntelAgent")
    
    # Internal documents
    if any(kw in prompt_lower for kw in ["internal", "document", "file", "report"]):
        required_agents.append("InternalDocsAgent")
    
    # If no specific agents selected, use core agents for comprehensive research
    if not required_agents:
        required_agents = [
            "MarketAgent",
            "ClinicalTrialsAgent",
            "PatentAgent",
            "WebIntelAgent"
        ]
    
    # Check if deep synthesis is needed (20+ citations, multi-year analysis)
    deep_synthesis_indicators = [
        "comprehensive",
        "full landscape",
        "20+ citations",
        "multi-year",
        "extensive",
        "systematic review",
        "meta-analysis",
        "deep dive"
    ]
    
    needs_deep_synthesis = any(indicator in prompt_lower for indicator in deep_synthesis_indicators)
    
    # Very long prompts might benefit from cloud
    is_very_long = len(prompt.split()) > 100
    
    return ModeClassification(
        mode=ChatMode.RESEARCH,
        required_agents=required_agents,
        needs_synthesis=True,
        needs_cloud=needs_deep_synthesis or is_very_long,  # Cloud only for deep synthesis
        reason=f"Research query - auto-routing to {len(required_agents)} specialized agents",
        priority=7
    )


def get_mode_explanation(classification: ModeClassification, engine: str) -> str:
    """
    Generate human-readable explanation for mode selection.
    
    Args:
        classification: ModeClassification result
        engine: Selected LLM engine ("local" or "cloud")
    
    Returns:
        str: Formatted explanation for timeline
    """
    mode_name = classification.mode.upper()
    
    engine_name = "Mistral-7B (Local)" if engine == "local" else f"{engine.upper()} (Cloud)"
    
    agent_info = ""
    if classification.required_agents:
        agent_count = len(classification.required_agents)
        agent_info = f"\nAgents: {agent_count} specialized agents"
    
    synthesis_info = ""
    if classification.needs_synthesis:
        synthesis_info = "\nSynthesis: Required"
    
    return f"""Mode selected: {mode_name}
Engine selected: {engine_name}
Reason: {classification.reason}{agent_info}{synthesis_info}"""


# Backward compatibility alias
def detect_mode(prompt: str, has_files: bool = False, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Legacy function for backward compatibility.
    Returns just the mode string.
    """
    meta = metadata or {}
    if has_files:
        meta["has_files"] = True
    
    classification = detect_research_mode(prompt, meta)
    return classification.mode
