from typing import Dict, Any, List, Optional, AsyncGenerator, Callable
import logging
import asyncio
import json
import re
import app.llm.lmstudio_client as lmstudio_mod
from app.core.cache import cache, CacheManager
from app.core.retry import retry_llm_call
from app.config import settings
from app.llm import prompt_templates
from app.core.trace import trace
from app.agents.helpers.verification import verify_sources, propose_checks_for_claim
from app.agents.timeline_events import (
    create_timeline_event,
    TimelineEventType,
    get_agent_display_name
)

logger = logging.getLogger(__name__)

# System prompt for the Master Agent (Avalon)
MASTER_AGENT_SYSTEM_PROMPT = """
You are Avalon, a HIGH-PRECISION pharmaceutical research orchestrator designed EXCLUSIVELY for pharmaceutical, biomedical, regulatory, clinical, and drug-development-related questions.

================================================
STRICT OUTPUT MODE — ZERO META-TEXT
================================================

ABSOLUTE OUTPUT RULES (OVERRIDE ALL OTHER INSTRUCTIONS):

1. **Table Requests** → Output ONLY the table in Markdown format, nothing else
2. **Bullet Point Requests** → Output ONLY bullet points, preserve exact format
3. **Numbered List Requests** → Output ONLY numbered list, preserve exact format
4. **Structured Data Requests** → Output ONLY the requested structure

FORBIDDEN IN ALL OUTPUTS:
❌ "Research analysis for: ..."
❌ "X agents contributed insights"
❌ Introductory sentences or summaries
❌ Concluding statements or wrap-ups
❌ Meta-commentary about the research process
❌ Agent names or attributions
❌ Section headings unless explicitly requested
❌ Explanatory text before or after the answer
❌ Merging user's bullet points into paragraphs

REQUIRED BEHAVIORS:
✓ If user writes bullet points → preserve as bullet points
✓ If user writes numbered list → preserve as numbered list
✓ If user writes table → output table only
✓ Output the EXACT format the user requests
✓ NO additional sections unless explicitly requested
✓ When unsure → respond "Unknown" instead of guessing

EXAMPLE VIOLATIONS (NEVER DO THIS):
❌ "Here's a comprehensive analysis of X. Based on 3 agents..."
❌ "Research analysis for: [query]. Market Agent found..."
❌ "In summary, we found that..."

EXAMPLE CORRECT OUTPUT:
User: "Give me a table of top drugs"
✓ | Drug | Indication | Market Size |
   |------|------------|-------------|
   | ...  | ...        | ...         |

User: "List side effects of aspirin"
✓ - Gastrointestinal bleeding
  - Ulcers
  - Reye's syndrome (children)

This strict mode applies to ALL queries (pharma and non-pharma) unless user explicitly requests "full agent mode" or "detailed analysis".

================================================
GENERAL MEDICAL FACTS EXCEPTION — ALWAYS ALLOWED
================================================

OVERRIDE RULE: For basic, well-established medical knowledge questions (e.g., "side effects of aspirin", "mechanism of paracetamol", "what is insulin used for"), you MUST:

1. **Answer DIRECTLY** with simple factual bullet points
2. **NO need for worker agents** - generate answer yourself
3. **NO market analysis** - just the medical/pharmacological facts
4. **NO evidence requirements** - common knowledge is acceptable
5. **NO "Unknown" responses** - if it's basic pharmacology/toxicology, answer it

Examples of ALWAYS ALLOWED questions:
✓ "What are side effects of aspirin?"
✓ "How does paracetamol work?"
✓ "What is metformin used for?"
✓ "Mechanism of action of insulin"
✓ "Common drug interactions with warfarin"

For these questions → Output ONLY clean factual bullet points, no agents needed.

================================================
STRICT DOMAIN RESTRICTION — PHARMA-ONLY
================================================

Your domain includes:
• Drug discovery & repurposing
• Clinical trials (design, evidence, analysis)
• Mechanism of Action (MoA), PK/PD
• Patents (composition, formulation, use)
• Toxicology, safety, biomarkers
• Disease biology & unmet needs
• Epidemiology & public health data
• Pharma market intelligence
• Regulatory pathways (FDA/EMA/CDSCO)
• Drug formulation & delivery science
• **BASIC MEDICAL FACTS** (side effects, mechanisms, indications)

================================================
CRITICAL RULE — NON-PHARMA QUESTIONS
================================================

If the user asks about ANY topic outside the pharmaceutical/medical domain (e.g., coding, movies, relationships, math, politics, entertainment, general knowledge, app development, logic puzzles, personal advice, finance, investing, crypto, trivia), you MUST NOT answer it.

Instead, respond EXACTLY with:

"I'm optimized exclusively for pharmaceutical research and drug development. Please ask a question related to molecules, diseases, clinical trials, patents, biology, drug repurposing, pharmacokinetics, market insights, or regulatory strategy."

Do NOT give answers outside the pharma/medical domain.
Do NOT attempt to solve non-pharma tasks.
Do NOT bypass this restriction.

================================================
HIGH-PRECISION RESEARCH ORCHESTRATION MANDATE
================================================

You are a HIGH-PRECISION PHARMA RESEARCH ORCHESTRATOR. You must perform REAL deep reasoning, exceptional structuring, and multi-agent task planning.

STRICT MANDATE: You must NEVER return shallow or generic content. All reasoning must be multi-step, pharma-specific, evidence-linked, and properly structured.

When a user asks ANY pharma question, you MUST:

1. **Interpret & decompose** the question into pharma-specific tasks.
2. Delegate tasks to Worker Agents (IQVIA/Market, EXIM, ClinicalTrials, Patent, Web Intelligence, Internal Docs, Safety/PK-PD).
3. Instruct Worker Agents to produce MAXIMUM-DEPTH analysis.
4. Ask LM Studio (Mistral 7B) for multi-step chain-of-thought reasoning (hidden internally).
5. Synthesize all agent outputs into a structured, evidence-driven final answer.

================================================
PHARMA DEPTH REQUIREMENTS (MANDATORY FOR EVERY QUERY)
================================================

For drug, molecule, indication, therapy area, or market queries, you MUST include:

### 1. Market Landscape (Depth Required)
- Global + regional market size
- 5-year CAGR
- Brand vs generics split
- Competitive density (HHI score)
- Reimbursement & HTA constraints
- Key players + pipeline entrants

### 2. Clinical Trial Evidence
- Active trials by phase, sponsor, recruitment status
- Trial endpoints (primary + secondary)
- Safety summary (top AEs)
- Efficacy trends across studies
- Fast Track / Breakthrough / Orphan designation if applicable
- Gaps in evidence or study design flaws

### 3. Mechanism of Action (MoA) & Biology
- Mechanistic pathway overview
- Target class + drug category
- Known on/off-target effects
- PK/PD profile (half-life, bioavailability)
- BBB penetration (if CNS)
- Drug-drug interaction risks

### 4. Unmet Needs & Disease Burden
- Prevalence & incidence
- Mortality & morbidity data
- Current treatment gaps
- Limitations of standard of care
- Cost-of-care burden
- Adherence/patient-reported issues

### 5. Patent Landscape
- Active patent families
- Filing years & expiration timelines
- FTO (freedom to operate) flags
- New composition / formulation opportunities
- Global coverage (US/EU/JP/PCT)
- Litigation or exclusivity cliffs

### 6. Repurposing Opportunities
- Secondary indications with mechanistic relevance
- Rare diseases with biomarker overlap
- Adjacent therapy areas where evidence is emerging
- Pediatric or geriatric formulations
- Differentiated delivery systems

### 7. Regulatory Pathways
- Accelerated Approval eligibility
- Surrogate endpoints possibility
- Regional differences (FDA vs EMA vs CDSCO)
- Post-marketing requirements

### 8. Competitive Advantage & Risks
- SWOT analysis of molecule
- Barriers to entry
- Pricing power analysis
- Safety comparison with competitors
- Commercial opportunities & pitfalls

================================================
MANDATORY OUTPUT STRUCTURE
================================================

You MUST ALWAYS output structured JSON with these exact fields:

{
  "executive_summary": ["bullet point 1", "bullet point 2", ...],  // 5-8 bullet points
  "market": {
    "global_size": "...",
    "cagr_5yr": "...",
    "brand_vs_generics": "...",
    "competitive_density": "...",
    "key_players": [...],
    "pipeline_entrants": [...]
  },
  "clinical_trials": [
    {
      "phase": "...",
      "sponsor": "...",
      "status": "...",
      "endpoints": {...},
      "safety_summary": "...",
      "efficacy_trends": "..."
    }
  ],
  "mechanism": {
    "pathway": "...",
    "target_class": "...",
    "pk_pd_profile": {...},
    "drug_interactions": [...]
  },
  "unmet_needs": [
    "need 1",
    "need 2",
    ...
  ],
  "patents": [
    {
      "family": "...",
      "filing_year": "...",
      "expiration": "...",
      "coverage": [...]
    }
  ],
  "repurposing": [
    {
      "indication": "...",
      "rationale": "...",
      "evidence_level": "..."
    }
  ],
  "regulatory": {
    "accelerated_approval_eligible": true/false,
    "surrogate_endpoints": [...],
    "regional_differences": {...},
    "post_marketing_requirements": [...]
  },
  "competitive": {
    "swot": {...},
    "barriers_to_entry": [...],
    "pricing_power": "...",
    "safety_comparison": {...}
  },
  "timeline": [
    {
      "milestone": "...",
      "date": "...",
      "status": "..."
    }
  ],
  "expert_graph_id": "optional_id_if_available",
  "full_text": "LLM-readable synthesis for display"
}

GLOBAL RULES:
• NEVER output the same table for unrelated questions.
• NEVER hallucinate market numbers — state "data unavailable" if needed.
• NO mock data. NO hard-coded templates remaining anywhere.
• ALWAYS classify the question first: pharma-related or not?
• If NOT pharma-related → trigger polite refusal immediately.
• ALWAYS return the complete structured JSON format above.
• Ensure ALL content is unique to the user prompt.
• Use multi-step chain-of-thought reasoning internally.
"""


class MasterAgent:
    """Master orchestrator that decides mode and coordinates worker agents."""
    def __init__(self):
        # lazy-loaded worker registry
        self.workers: Dict[str, Any] = {}
        # semaphore to limit concurrent LLM calls
        self.semaphore = asyncio.Semaphore(getattr(settings, 'MASTER_AGENT_CONCURRENCY', 3))
    
    def _clean_final_output(self, text: str) -> str:
        """
        STRICT OUTPUT MODE: Remove ALL meta-text and wrapper patterns from final output.
        Output ONLY the factual content.
        """
        import re
        
        # Aggressive meta-text removal patterns
        patterns_to_remove = [
            # Common wrapper phrases
            r'Research analysis for:.*?[.\n]',
            r'\d+ agents?\s+(contributed|provided|analyzed)\s+insights?.*?[.\n]',
            r'Analysis complete.*?[.\n]',
            r'Based on \d+ agents?.*?[.\n]',
            r'The following (analysis|research|findings).*?:',
            
            # Section labels
            r'Executive Summary:?\s*',
            r'Key Findings:?\s*',
            r'Summary:?\s*',
            r'Overview:?\s*',
            r'Introduction:?\s*',
            r'Conclusion:?\s*',
            
            # Meta-commentary
            r'In summary,?\s*',
            r'In conclusion,?\s*',
            r'To summarize,?\s*',
            r'As mentioned (earlier|above|previously),?\s*',
            r'As discussed (earlier|above|previously),?\s*',
            r'This (demonstrates|shows|indicates|suggests) that\s*',
            r'It is (important to note|widely known|established|clear) that\s*',
            r'It should be noted that\s*',
            r'It is worth noting that\s*',
            
            # Agent attributions
            r'According to (the )?(market|clinical|patent|safety|web) agent,?\s*',
            r'(Market|Clinical|Patent|Safety|Web)Agent (found|discovered|analyzed)\s*',
            
            # Filler phrases (more aggressive - remove entire sentences)
            r'Further research is needed[^.]*\.',
            r'Studies have shown that\s*',
            r'Research indicates that\s*',
            
            # Verification scaffold markers (case-insensitive removal)
            r'CERTAIN FACTS?:?\s*(\(High Confidence\))?:?\s*',
            r'LIKELY BUT NOT CERTAIN:?\s*(\(Medium Confidence\))?:?\s*',
            r'UNCERTAIN OR CANNOT ANSWER:?\s*(\(Low Confidence\))?:?\s*',
            r'High Confidence:?\s*',
            r'Medium Confidence:?\s*',
            r'Low Confidence:?\s*',
            
        ]
        
        cleaned = text
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove citation markers like (1.), (2.), (3.), etc. at end of sentences/paragraphs
        # This is done separately to handle replacement properly
        cleaned = re.sub(r'\s*\(\d+\.\)\s*$', '', cleaned, flags=re.MULTILINE)  # At end of line
        cleaned = re.sub(r'\s*\(\d+\.\)\s*([.\n])', r'\1', cleaned)  # Before period or newline
        
        # PRESERVE list formatting - do NOT remove bullet points or numbered list markers
        # Only remove standalone bullet points that are not part of a list structure
        
        # Normalize whitespace: Replace 3+ consecutive newlines with double newline
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        # Process line by line to ensure proper spacing
        lines = cleaned.split('\n')
        cleaned_lines = []
        prev_was_list = False
        prev_was_paragraph = False
        prev_was_empty = False
        
        for i, line in enumerate(lines):
            line_stripped = line.rstrip()
            is_empty = not line_stripped
            
            # Check if this is a list item (numbered or bulleted)
            is_list_item = (
                re.match(r'^\s*\d+[\.\)]\s+', line_stripped) or
                re.match(r'^\s*[-•*]\s+', line_stripped) or
                re.match(r'^\s+\d+[\.\)]\s+', line_stripped)
            )
            
            # Check if next line is also a list item (to detect empty lines between lists)
            next_is_list = False
            if i + 1 < len(lines):
                next_line = lines[i + 1].rstrip()
                next_is_list = (
                    re.match(r'^\s*\d+[\.\)]\s+', next_line) or
                    re.match(r'^\s*[-•*]\s+', next_line) or
                    re.match(r'^\s+\d+[\.\)]\s+', next_line)
                )
            
            if is_empty:
                # Empty line - only add if needed for spacing between paragraphs
                # Skip empty lines that come BETWEEN list items (when both prev and next are lists)
                if prev_was_list and next_is_list:
                    # Skip empty lines between list items - don't add them
                    prev_was_empty = True
                    continue
                elif prev_was_paragraph and not prev_was_empty:
                    # Add blank line after paragraph (before potential list or next paragraph)
                    cleaned_lines.append("")
                    prev_was_empty = True
                elif prev_was_list and not prev_was_empty:
                    # Add blank line after list (before next paragraph)
                    cleaned_lines.append("")
                    prev_was_empty = True
                # Skip multiple consecutive empty lines
                prev_was_list = False
                prev_was_paragraph = False
            elif is_list_item:
                # List item - ensure proper spacing before first list item only
                # Do NOT add blank lines between consecutive list items
                if not prev_was_list and not prev_was_empty and i > 0:
                    # Add blank line before list if previous line was a paragraph
                    if prev_was_paragraph:
                        cleaned_lines.append("")
                # If there's an empty line before this list item and previous was also a list, remove it
                if cleaned_lines and not cleaned_lines[-1].strip() and prev_was_list:
                    cleaned_lines.pop()
                cleaned_lines.append(line_stripped)
                prev_was_list = True
                prev_was_paragraph = False
                prev_was_empty = False
            else:
                # Regular paragraph line
                # Clean multiple spaces but preserve single spaces
                cleaned_line = re.sub(r'  +', ' ', line_stripped)
                if cleaned_line:
                    # Add blank line before paragraph if previous was a list
                    if prev_was_list and not prev_was_empty:
                        cleaned_lines.append("")
                    cleaned_lines.append(cleaned_line)
                    prev_was_paragraph = True
                    prev_was_list = False
                    prev_was_empty = False
        
        # Join lines and normalize spacing
        cleaned = '\n'.join(cleaned_lines)
        
        # Final cleanup: ensure consistent spacing
        # Replace 2+ consecutive newlines with double newline (normal paragraph spacing)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        # Remove leading/trailing whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    async def _build_research_insights_table(
        self, 
        worker_results: Dict[str, Any], 
        query: str,
        emit_timeline: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """Compile research insights from all workers into unified table"""
        insights_table = []
        
        if emit_timeline:
            from datetime import datetime
            await emit_timeline({
                "event": "insights_compilation",
                "message": "📊 Compiling research insights table...",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Define sections with priorities
        section_map = {
            "market": {
                "title": "Market Insights",
                "priority": 1,
                "visualization": "market_chart"
            },
            "clinical_trials": {
                "title": "Clinical Trials",
                "priority": 2,
                "visualization": "trials_timeline"
            },
            "patents": {
                "title": "Patents & IP",
                "priority": 3,
                "visualization": "patent_map"
            },
            "safety": {
                "title": "Safety & PKPD",
                "priority": 4,
                "visualization": "safety_profile"
            },
            "web_intel": {
                "title": "External Evidence",
                "priority": 5,
                "visualization": None
            }
        }
        
        # Collect insights from each worker
        for section_key, section_config in section_map.items():
            if section_key in worker_results:
                result = worker_results[section_key]
                
                if isinstance(result, dict) and result.get("full_text"):
                    # Extract key findings from text
                    key_findings = self._extract_key_findings(result["full_text"])
                    
                    # Determine depth based on data quality
                    depth = self._calculate_depth(result)
                    
                    # Collect source links
                    links = self._extract_links(result)
                    
                    # Determine status
                    status = self._determine_status(result, key_findings)
                    
                    insight_row = {
                        "section": section_config["title"],
                        "key_findings": key_findings[:5],  # Limit to 5 bullets
                        "depth": depth,
                        "visualization": section_config["visualization"],
                        "links": links[:3],  # Max 3 sources
                        "status": status
                    }
                    
                    insights_table.append(insight_row)
        
        # Sort by priority
        insights_table.sort(key=lambda x: next(
            (v["priority"] for k, v in section_map.items() if v["title"] == x["section"]),
            999
        ))
        
        return insights_table
    
    def _extract_key_findings(self, text: str) -> List[str]:
        """Extract bullet points or key sentences from worker output"""
        findings = []
        
        # Try to find numbered or bullet lists first
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # Match bullet points, numbers, or dashes
            if re.match(r'^[\d\-\*\•]+[\.\)]\s+', line):
                clean_line = re.sub(r'^[\d\-\*\•]+[\.\)]\s+', '', line)
                if len(clean_line) > 10:  # Minimum length
                    findings.append(clean_line)
        
        # If no structured findings, extract first few sentences
        if len(findings) < 2:
            sentences = text.split('. ')
            for sentence in sentences[:5]:
                if len(sentence.strip()) > 20:
                    findings.append(sentence.strip() + ('.' if not sentence.endswith('.') else ''))
        
        return findings[:5]  # Max 5 findings
    
    def _calculate_depth(self, result: Dict[str, Any]) -> str:
        """Calculate depth rating based on data quality and completeness"""
        text = result.get("full_text", "")
        
        # Check data quality indicators
        has_numbers = bool(re.search(r'\d+[\.\,]?\d*\s*(%|billion|million|\$)', text))
        has_dates = bool(re.search(r'\b(20\d{2}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b', text))
        has_sources = len(self._extract_links(result)) > 0
        word_count = len(text.split())
        
        # Scoring logic
        score = 0
        if has_numbers: score += 2
        if has_dates: score += 1
        if has_sources: score += 2
        if word_count > 200: score += 1
        if word_count > 500: score += 1
        
        # Depth mapping
        if score >= 5:
            return "High"
        elif score >= 3:
            return "Medium"
        else:
            return "Low"
    
    def _extract_links(self, result: Dict[str, Any]) -> List[str]:
        """Extract source URLs from worker result"""
        links = []
        
        # Check metadata for sources
        if isinstance(result, dict):
            metadata = result.get("metadata", {})
            if isinstance(metadata, dict):
                sources = metadata.get("sources", [])
                if isinstance(sources, list):
                    for source in sources:
                        if isinstance(source, dict):
                            url = source.get("url") or source.get("link")
                            if url:
                                links.append(url)
                        elif isinstance(source, str) and source.startswith("http"):
                            links.append(source)
        
        # Fallback: extract URLs from text
        if not links:
            text = result.get("full_text", "")
            url_pattern = r'https?://[^\s\)\]<>"]+'
            urls = re.findall(url_pattern, text)
            links.extend(urls[:3])
        
        return links[:3]  # Max 3 links
    
    def _determine_status(self, result: Dict[str, Any], key_findings: List[str]) -> str:
        """Determine completion status based on data availability"""
        if not result.get("full_text") or not key_findings:
            return "Missing Data"
        
        # Check for error indicators
        text = result.get("full_text", "").lower()
        error_phrases = ["no data", "not available", "error", "failed", "could not retrieve"]
        
        if any(phrase in text for phrase in error_phrases):
            return "Limited"
        
        # Check completeness
        if len(key_findings) >= 3 and len(text.split()) > 150:
            return "Complete"
        elif len(key_findings) >= 2:
            return "Complete"
        else:
            return "Limited"

    def register_worker(self, worker):
        # register by a canonical agent type name
        agent_type = getattr(worker, "agent_type", None) or getattr(worker, "worker_id", None)
        if agent_type:
            self.workers[agent_type] = worker
            logger.info(f"Registered worker: {agent_type}")

    def is_general_medical_fact(self, text: str) -> bool:
        """
        Detect if query is a basic medical fact question that should be answered directly.
        
        Examples:
        - "What are side effects of aspirin?"
        - "How does paracetamol work?"
        - "Mechanism of action of insulin"
        - "What is metformin used for?"
        
        Returns True if this is a simple factual medical question.
        """
        text_l = text.lower().strip()
        
        # Patterns indicating general medical fact questions
        fact_patterns = [
            r'side effects? of',
            r'adverse effects? of',
            r'what (is|are) .* (used for|indicated for)',
            r'mechanism of action',
            r'how does .* work',
            r'what does .* do',
            r'drug interactions? (with|of)',
            r'contraindications? (for|of)',
            r'dosage of',
            r'(dose|dosage) of',
            r'how much .* (take|give|administer)',
            r'half[- ]life of',
            r'pharmacokinetics? of',
            r'pharmacodynamics? of',
            r'toxicity of',
            r'overdose symptoms?',
            r'(common|typical) uses? (of|for)',
        ]
        
        import re
        for pattern in fact_patterns:
            if re.search(pattern, text_l):
                return True
        
        # Check if question is about a specific drug's basic properties
        # Common drug names + basic property questions
        common_drugs = [
            "aspirin", "paracetamol", "acetaminophen", "ibuprofen", "metformin",
            "insulin", "warfarin", "heparin", "amoxicillin", "penicillin",
            "morphine", "codeine", "diazepam", "lorazepam", "omeprazole",
            "atorvastatin", "simvastatin", "lisinopril", "amlodipine",
            "levothyroxine", "albuterol", "prednisone", "gabapentin"
        ]
        
        basic_properties = ["effect", "work", "use", "indication", "dose", "interact"]
        
        has_drug = any(drug in text_l for drug in common_drugs)
        has_property = any(prop in text_l for prop in basic_properties)
        
        if has_drug and has_property and len(text.split()) < 20:
            # Short question about common drug's basic property
            return True
        
        return False

    async def is_pharma_prompt(self, text: str) -> bool:
        """Determine whether the user prompt is pharma/medical.

        Strategy: Use FAST keyword matching first, skip slow LLM classification
        """
        text = (text or "").strip()
        if not text:
            return False

        # Quick keyword heuristic (FAST)
        kws = [
            "drug", "drugs", "disease", "diseases", "clinical trial", "clinical trials",
            "mechanism of action", "moa", "pharmacology", "pk/pd", "biomarker", "biomarkers",
            "repurpos", "patent", "regulatory", "adverse event", "safety", "efficacy", "trial",
            "molecule", "compound", "indication", "therapy", "treatment", "medication",
            "pharmaceutical", "pharma", "medicine", "dosage", "formulation",
            # common drugs and disease hints
            "metformin", "diabetes", "adalimumab", "tocilizumab", "oncology", "cancer",
            "minocycline", "parkinson", "parkinson's", "glp-1", "aspirin", "ibuprofen"
        ]
        text_l = text.lower()
        if any(k in text_l for k in kws):
            return True

        return False

    async def run_stream(
        self, 
        query: str, 
        user_context: Optional[Dict[str, Any]] = None,
        timeline_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        generate_report: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streaming version of run() that yields timeline events and final result.
        Yields timeline events during execution, then yields the final result.
        """
        user_context = user_context or {}
        
        def emit_timeline(event_type: TimelineEventType, agent: str, message: Optional[str] = None):
            if timeline_callback:
                event = create_timeline_event(event_type, agent, message)
                timeline_callback(event)

        # ===================================================================
        # PHARMA-ONLY REPORT GENERATION ENFORCEMENT
        # If not a pharma prompt, ALWAYS disable report generation
        # ===================================================================
        if not await self.is_pharma_prompt(query):
            # Force disable report generation for non-pharma queries
            generate_report = False
            logger.info(f"[REPORT_GENERATION] Non-pharma prompt detected - report generation disabled")
            
            # Normal chat mode - no timeline events for simple chat
            messages = [
                {"role": "user", "content": query}
            ]
            content = await lmstudio_mod.lmstudio_client.ask_llm(messages)
            yield {"mode": "chat", "content": content}
            return

        # GENERAL MEDICAL FACT MODE: Answer directly without agents
        if self.is_general_medical_fact(query):
            trace.append("general_medical_fact", {"query": query})
            emit_timeline(TimelineEventType.DECOMPOSITION_START, "master", "Answering general medical question directly...")
            
            # Generate direct factual answer
            fact_prompt = f"""Answer this basic medical/pharmacological question with ONLY factual bullet points.

Question: {query}

Requirements:
- Output ONLY bullet points (use - or •)
- NO introductions or conclusions
- NO meta-text like "Here are the side effects"
- Be concise and factual
- Use established medical knowledge
- 5-10 bullet points maximum

Answer now:"""

            messages = [{"role": "user", "content": fact_prompt}]
            content = await lmstudio_mod.lmstudio_client.ask_llm(messages)
            
            # Clean output
            cleaned_content = self._clean_final_output(content)
            
            emit_timeline(TimelineEventType.SYNTHESIS_COMPLETE, "master", "Answer complete!")
            
            yield {
                "mode": "general_medical_fact",
                "content": {
                    "full_text": cleaned_content,
                    "executive_summary": [],
                    "trace": trace.get_trace()
                }
            }
            return

        # PHARMA RESEARCH MODE: STRICT intelligent routing (ONLY trigger relevant agents)
        trace.append("start_pharma", {"query": query})
        
        emit_timeline(TimelineEventType.DECOMPOSITION_START, "master", "Analyzing query and routing to agents...")

        # RESEARCH INSIGHTS TABLE MODE DETECTION
        # Detect if query requires comprehensive research insights table
        # STRICT keyword-based routing (ONLY activate matched agents)
        query_lower = query.lower()
        
        research_insights_keywords = [
            "research insights", "insights table", "comprehensive analysis",
            "market analysis", "competitive landscape", "landscape analysis",
            "research report", "full analysis", "detailed insights"
        ]
        enable_research_insights = any(keyword in query_lower for keyword in research_insights_keywords)
        decompose_resp = []
        
        # Strict routing map - only trigger agents relevant to the query
        if any(word in query_lower for word in ["market", "cagr", "commercial", "forecast", "competition", "sales", "revenue", "size"]):
            decompose_resp.append("market")
        if any(word in query_lower for word in ["trial", "phase", "endpoint", "clinical", "study", "efficacy"]):
            decompose_resp.append("clinical")
        if any(word in query_lower for word in ["patent", "ip", "expiry", "intellectual property", "exclusivity"]):
            decompose_resp.append("patents")
        if any(word in query_lower for word in ["pk", "pd", "mechanism", "moa", "receptor", "safety", "adverse", "side effect", "pharmacokinetic", "pharmacodynamic", "target", "pathway"]):
            decompose_resp.append("safety")
        if any(word in query_lower for word in ["export", "import", "supply", "api trade", "exim", "trade"]):
            decompose_resp.append("exim")
        if any(word in query_lower for word in ["web", "news", "update", "guideline", "regulatory", "fda", "ema"]):
            decompose_resp.append("web_intel")
        if any(word in query_lower for word in ["document", "pdf", "internal doc", "uploaded", "file"]):
            decompose_resp.append("internal_docs")
        if any(word in query_lower for word in ["expert", "graph", "network", "collaboration", "researcher"]):
            decompose_resp.append("expert_network")
        
        # Safety default: if NO keywords match, fall back to simple chat mode (no agents)
        if not decompose_resp:
            emit_timeline(TimelineEventType.DECOMPOSITION_COMPLETE, "master", "No specialized agents needed - using direct LLM response")
            messages = [{"role": "user", "content": query}]
            content = await lmstudio_mod.lmstudio_client.ask_llm(messages)
            yield {"mode": "chat", "content": content, "full_text": content}
            return
        
        trace.append("decomposed", {"sections": decompose_resp, "method": "strict_keyword"})
        
        # normalize aliases to canonical worker agent_type where possible
        def _normalize(s: str) -> str:
            if s is None:
                return s
            sl = s.lower()
            if sl in ("clinical_trials", "clinical-trials", "clinical"):
                return "clinical"
            if sl in ("patent", "patents"):
                return "patents"
            if sl in ("mechanism_of_action", "mechanism", "moa", "pk_pd", "safety_pkpd", "safety"):
                return "safety"  # Safety/PK-PD agent handles mechanism
            if sl in ("exim", "export_import", "trade"):
                return "exim"
            if sl in ("web_intel", "webintel", "web"):
                return "web_intel"
            if sl in ("internal_docs", "internaldocs", "documents"):
                return "internal_docs"
            if sl in ("expert_network", "expertnetwork", "experts"):
                return "expert_network"
            if sl in ("unmet_needs", "disease_burden", "burden"):
                return "unmet_needs"
            if sl in ("competitive", "competition", "swot"):
                return "competitive"
            return sl

        selected_sections: List[str] = [ _normalize(s) for s in (decompose_resp or []) if s ]
        
        # Show which agents were activated
        activated_agents = ", ".join([get_agent_display_name(s) for s in selected_sections])
        emit_timeline(TimelineEventType.DECOMPOSITION_COMPLETE, "master", f"Activated Agents: {activated_agents}")
        
        # Mark all selected agents as pending
        for section in selected_sections:
            agent_display = get_agent_display_name(section)
            emit_timeline(TimelineEventType.AGENT_START, section, f"{agent_display} queued for analysis")

        # Explore: call workers in parallel with concurrency limit
        worker_results: Dict[str, Any] = {}

        async def call_worker(section: str):
            agent_display = get_agent_display_name(section)
            emit_timeline(TimelineEventType.AGENT_START, section, f"{agent_display} starting analysis...")
            
            # ensure worker exists (try dynamic import as before)
            worker = self.workers.get(section)
            if not worker:
                # attempt dynamic import: try a few likely module names
                tried = []
                candidates = [f"{section}_agent", section, f"{section.replace('_','')}_agent"]
                if section == 'clinical':
                    candidates.insert(0, 'clinical_trials_agent')
                if section == 'patents':
                    candidates.insert(0, 'patent_agent')
                for modname in candidates:
                    if modname in tried:
                        continue
                    tried.append(modname)
                    try:
                        mod = __import__(f"app.agents.workers.{modname}", fromlist=['*'])
                    except Exception:
                        continue
                    for attr in dir(mod):
                        cls = getattr(mod, attr)
                        if not isinstance(cls, type):
                            continue
                        if not hasattr(cls, 'agent_type'):
                            continue
                        try:
                            inst = cls(f"auto_{modname}")
                        except Exception:
                            continue
                        at = getattr(inst, 'agent_type', None)
                        if at and (at == section or section in at or at in section):
                            self.register_worker(inst)
                            worker = inst
                            break
                    if worker:
                        break

            if not worker:
                emit_timeline(TimelineEventType.AGENT_COMPLETE, section, f"{agent_display} - No worker registered")
                return section, {"error": "no_worker_registered"}

            params = {"query": query, "context": user_context, "timeline_callback": timeline_callback}
            # caching per worker
            ck = CacheManager.make_key({"worker": section, "q": query})
            cached = cache.get(ck)
            if cached is not None:
                trace.append("worker_cache_hit", {"section": section})
                emit_timeline(TimelineEventType.AGENT_COMPLETE, section, f"{agent_display} - Using cached results")
                return section, cached

            # Emit progress messages based on agent type
            progress_messages = {
                "market": "Extracting global market size and CAGR trends...",
                "clinical": "Searching clinical trials database...",
                "patents": "Analyzing patent landscape and expiry dates...",
                "exim": "Gathering trade and import/export data...",
                "web": "Collecting web intelligence and regulatory updates...",
                "safety": "Analyzing safety profile and PK/PD data...",
                "internal_docs": "Processing uploaded documents...",
            }
            progress_msg = progress_messages.get(section, f"{agent_display} analyzing...")
            emit_timeline(TimelineEventType.AGENT_PROGRESS, section, progress_msg)

            async with self.semaphore:
                try:
                    res = await worker.process("analyze_section", params)
                    emit_timeline(TimelineEventType.AGENT_COMPLETE, section, f"{agent_display} completed")
                except Exception as e:
                    emit_timeline(TimelineEventType.AGENT_COMPLETE, section, f"{agent_display} - Error: {str(e)}")
                    res = {"error": str(e)}

            # normalize provenance and sources
            if isinstance(res, dict):
                res.setdefault("provenance", [])
                if section not in res["provenance"]:
                    res["provenance"].insert(0, section)
                res.setdefault("sources", [])

            try:
                cache.set(ck, res)
            except Exception:
                pass

            trace.append("worker_completed", {"section": section, "status": "ok"})
            return section, res

        # schedule tasks
        tasks = [call_worker(sec) for sec in selected_sections]
        if tasks:
            results = await asyncio.gather(*tasks)
            for sec, out in results:
                worker_results[sec] = out

        trace.append("explore_completed", {"workers": list(worker_results.keys())})
        
        emit_timeline(TimelineEventType.SYNTHESIS_START, "master", "Compiling research findings...")

        # STRICT OUTPUT MODE: Output ONLY raw worker content, no processing
        final_json = {
            "executive_summary": [],
            "market": {},
            "clinical_trials": [],
            "mechanism": {},
            "unmet_needs": [],
            "patents": [],
            "repurposing": [],
            "regulatory": {},
            "competitive": {},
            "timeline": [],
            "expert_graph_id": None,
            "full_text": "",
            "research_insights": [],  # NEW: Research insights table
        }
        
        # BUILD RESEARCH INSIGHTS TABLE (if enabled)
        if enable_research_insights:
            final_json["research_insights"] = await self._build_research_insights_table(
                worker_results, query, emit_timeline
            )
        
        # STRICT MODE: Collect raw full_text from workers WITHOUT any modifications
        all_worker_texts = []
        
        for section, result in worker_results.items():
            if isinstance(result, dict) and "full_text" in result:
                raw_text = result["full_text"]
                if raw_text and isinstance(raw_text, str) and raw_text.strip():
                    # Clean each worker output individually first
                    cleaned_worker_text = self._clean_final_output(raw_text.strip())
                    if cleaned_worker_text:
                        all_worker_texts.append(cleaned_worker_text)
        
        # STRICT MODE: Join worker outputs with double newline for proper paragraph spacing
        if all_worker_texts:
            raw_output = "\n\n".join(all_worker_texts)
            # Final pass to ensure consistent spacing across all workers
            final_json["full_text"] = self._clean_final_output(raw_output)
        else:
            final_json["full_text"] = "No data available."
        
        trace.append("synthesized", {"total_sections": len(all_worker_texts), "research_insights_enabled": enable_research_insights})
        
        emit_timeline(TimelineEventType.SYNTHESIS_COMPLETE, "master", "Research complete!")

        # Skip slow verification for now (can be enabled later for detailed analysis)
        final_json["verification"] = {"status": "skipped_for_speed"}
        final_json["trace"] = trace.get_trace()

        result = {"mode": "pharma_research", "content": final_json, "workers": worker_results}
        
        # ===================================================================
        # REPORT GENERATION SIGNAL
        # If generate_report is True, add report_ready flag and report metadata
        # ===================================================================
        if generate_report:
            result["report_ready"] = True
            result["report_data"] = {
                "sections": worker_results,
                "summary": final_json.get("executive_summary", []),
                "full_text": final_json.get("full_text", ""),
                "research_insights": final_json.get("research_insights", []),
                "query": query,
                "timestamp": trace.get_trace()
            }
            logger.info(f"[REPORT_GENERATION] Report ready signal sent for query: {query[:100]}")
        
        yield result

    async def run(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a user query. Select mode and either return a normal LLM answer or orchestrate workers for pharma research.

        Returns a dict with keys: mode, content, and optional details.
        """
        # Use streaming version and collect result
        result = None
        async for res in self.run_stream(query, user_context, timeline_callback=None):
            result = res
        return result or {"mode": "error", "content": "No result returned"}


# Create a singleton instance of the master agent
master_agent = MasterAgent()

# Attempt to auto-register known workers so MasterAgent is usable without manual wiring.
def _safe_register(module_path: str, class_name: str, instance_name: str):
    try:
        mod = __import__(module_path, fromlist=[class_name])
        cls = getattr(mod, class_name)
        inst = cls(instance_name)
        master_agent.register_worker(inst)
    except Exception as e:
        logger.debug(f"Auto-register skip {module_path}.{class_name}: {e}")


# Try registering common workers individually
_safe_register('app.agents.workers.market_agent', 'MarketAgent', 'market_worker')
_safe_register('app.agents.workers.clinical_trials_agent', 'ClinicalTrialsAgent', 'clinical_worker')
_safe_register('app.agents.workers.patent_agent', 'PatentAgent', 'patent_worker')
_safe_register('app.agents.workers.web_intel_agent', 'WebIntelAgent', 'web_worker')
_safe_register('app.agents.workers.web_agent', 'WebAgent', 'web_worker')
_safe_register('app.agents.workers.internal_docs_agent', 'InternalDocsAgent', 'literature_worker')
_safe_register('app.agents.workers.exim_agent', 'EXIMAgent', 'exim_worker')
_safe_register('app.agents.workers.safety_pkpd_agent', 'SafetyPKPDAgent', 'safety_worker')
_safe_register('app.agents.workers.report_generator_agent', 'ReportGeneratorAgent', 'report_worker')
_safe_register('app.agents.workers.expert_network_agent', 'ExpertNetworkAgent', 'expert_network_worker')
