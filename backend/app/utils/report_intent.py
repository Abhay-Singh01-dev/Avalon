"""
Report Intent Detector
Determines when Avalon should automatically generate a downloadable research report.
"""

import re
from typing import List


def should_generate_report(prompt: str, mode: str, uploaded_files_count: int) -> bool:
    """
    Determines if a research report should be automatically generated.
    
    Args:
        prompt: The user's input message
        mode: Current chat mode (e.g., "document", "research", "chat")
        uploaded_files_count: Number of files uploaded by the user
    
    Returns:
        bool: True if a report should be generated, False otherwise
    
    Rules:
        1. EXPLICIT REQUESTS → ALWAYS TRUE
        2. MULTI-SECTION / MULTI-AGENT PROMPT → TRUE (3+ pharma domains)
        3. MODE TRIGGER → TRUE for "document" or "research" modes
        4. MULTIPLE UPLOADED FILES → TRUE (2+ files)
        5. SIMPLE PROMPTS → FALSE
    """
    
    if not prompt:
        return False
    
    prompt_lower = prompt.lower()
    
    # =====================================================
    # RULE 1: EXPLICIT REQUESTS → ALWAYS TRUE
    # =====================================================
    explicit_keywords = [
        "report",
        "generate report",
        "make a report",
        "pdf",
        "professional summary",
        "structured report",
        "research report",
        "make an analysis document",
        "create a dossier",
        "comprehensive report",
        "detailed report",
        "analysis report",
        "full report",
        "export report"
    ]
    
    for keyword in explicit_keywords:
        if keyword in prompt_lower:
            return True
    
    # =====================================================
    # RULE 2: MULTI-SECTION / MULTI-AGENT PROMPT → TRUE
    # Check for 3+ pharma research domains
    # =====================================================
    pharma_domains = [
        "market",
        "trial",
        "trials",
        "patent",
        "patents",
        "pk",  # pharmacokinetics
        "pd",  # pharmacodynamics
        "mechanism",
        "moa",  # mechanism of action
        "regulatory",
        "safety",
        "competition",
        "competitive",
        "forecast",
        "forecasting",
        "approval",
        "clinical",
        "efficacy",
        "toxicity",
        "pharmacology"
    ]
    
    domain_matches = sum(1 for domain in pharma_domains if domain in prompt_lower)
    
    if domain_matches >= 3:
        return True
    
    # =====================================================
    # RULE 3: MODE TRIGGER → TRUE for document/research modes
    # =====================================================
    if mode and mode.lower() in ["document", "research"]:
        return True
    
    # =====================================================
    # RULE 4: MULTIPLE UPLOADED FILES → TRUE
    # =====================================================
    if uploaded_files_count >= 2:
        return True
    
    # =====================================================
    # RULE 5: SIMPLE PROMPTS → FALSE
    # Check if prompt is short, single-topic, basic, or question-only
    # =====================================================
    
    # If we reach here, check if it's a simple prompt
    # Simple prompts are typically:
    # - Short (< 50 characters)
    # - Single sentence questions
    # - Basic factual queries
    
    words = prompt.split()
    
    # Very short prompts are likely simple
    if len(words) < 10 and len(prompt) < 50:
        # Check if it's just a basic question
        simple_question_patterns = [
            r"^what is\b",
            r"^what's\b",
            r"^how does\b",
            r"^why does\b",
            r"^when was\b",
            r"^where is\b",
            r"^who is\b",
            r"^explain\b",
            r"^define\b",
            r"^tell me about\b"
        ]
        
        for pattern in simple_question_patterns:
            if re.match(pattern, prompt_lower):
                return False
    
    # If we've made it here and none of the above rules triggered,
    # default to False (no report)
    return False


def count_pharma_domains(prompt: str) -> int:
    """
    Helper function to count how many pharma research domains are mentioned.
    
    Args:
        prompt: The user's input message
    
    Returns:
        int: Number of pharma domains detected
    """
    pharma_domains = [
        "market",
        "trial",
        "trials",
        "patent",
        "patents",
        "pk",
        "pd",
        "mechanism",
        "moa",
        "regulatory",
        "safety",
        "competition",
        "competitive",
        "forecast",
        "forecasting",
        "approval",
        "clinical",
        "efficacy",
        "toxicity",
        "pharmacology"
    ]
    
    prompt_lower = prompt.lower()
    return sum(1 for domain in pharma_domains if domain in prompt_lower)
