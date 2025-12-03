"""Unified response schema enforcer for all worker agents."""
from typing import Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)


def get_unified_schema_template(agent_name: str) -> Dict[str, Any]:
    """Get the base unified schema template with all required fields."""
    return {
        "agent_name": agent_name,
        "agent_version": "1.0",
        "query_understanding": {
            "original_query": "",
            "intent": "",
            "subtasks": []
        },
        "core_findings": {
            "summary": [],
            "detailed_points": []
        },
        "tables": [],
        "key_insights": [],
        "timeline": [],
        "citations": [],
        "confidence_score": {
            "value": 0.0,
            "explanation": ""
        }
    }


def normalize_to_unified_schema(
    agent_name: str,
    llm_output: Dict[str, Any],
    original_query: str = ""
) -> Dict[str, Any]:
    """
    Normalize LLM output to the unified schema.
    Ensures all required fields are present, even if empty.
    """
    template = get_unified_schema_template(agent_name)
    
    # Start with template
    normalized = template.copy()
    
    # Extract query understanding
    if "query_understanding" in llm_output:
        normalized["query_understanding"].update(llm_output["query_understanding"])
    normalized["query_understanding"]["original_query"] = original_query or llm_output.get("original_query", "")
    
    # Extract core findings
    if "core_findings" in llm_output:
        if "summary" in llm_output["core_findings"]:
            normalized["core_findings"]["summary"] = llm_output["core_findings"]["summary"]
        if "detailed_points" in llm_output["core_findings"]:
            normalized["core_findings"]["detailed_points"] = llm_output["core_findings"]["detailed_points"]
    # Fallback: try to extract from old format
    elif "summary" in llm_output:
        if isinstance(llm_output["summary"], list):
            normalized["core_findings"]["summary"] = llm_output["summary"]
        else:
            normalized["core_findings"]["summary"] = [llm_output["summary"]]
    
    # Extract tables
    if "tables" in llm_output:
        normalized["tables"] = llm_output["tables"]
    # Fallback: try to construct from details
    elif "details" in llm_output and isinstance(llm_output["details"], dict):
        # Try to extract table-like structures
        tables = []
        for key, value in llm_output["details"].items():
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                # Try to infer table structure
                if "title" in value[0] or any(k in value[0] for k in ["metric", "value", "nct_id", "patent_id"]):
                    tables.append({
                        "title": key.replace("_", " ").title(),
                        "columns": list(value[0].keys()) if value else [],
                        "rows": [[str(v) for v in row.values()] for row in value[:10]],  # Limit rows
                        "interpretation": f"Data extracted from {key}"
                    })
        normalized["tables"] = tables
    
    # Extract key insights
    if "key_insights" in llm_output:
        normalized["key_insights"] = llm_output["key_insights"]
    
    # Extract timeline
    if "timeline" in llm_output:
        normalized["timeline"] = llm_output["timeline"]
    
    # Extract citations
    if "citations" in llm_output:
        normalized["citations"] = llm_output["citations"]
    # Fallback: try to extract from sources
    elif "sources" in llm_output:
        sources = llm_output["sources"] if isinstance(llm_output["sources"], list) else [llm_output["sources"]]
        normalized["citations"] = [
            {
                "source": str(s) if isinstance(s, str) else s.get("source", ""),
                "url": s.get("url", "") if isinstance(s, dict) else "",
                "type": s.get("type", "database") if isinstance(s, dict) else "database",
                "quote": s.get("quote", "") if isinstance(s, dict) else ""
            }
            for s in sources
        ]
    
    # Extract confidence score
    if "confidence_score" in llm_output:
        normalized["confidence_score"] = llm_output["confidence_score"]
    elif "confidence" in llm_output:
        conf_value = llm_output["confidence"]
        if isinstance(conf_value, (int, float)):
            normalized["confidence_score"]["value"] = float(conf_value) / 100.0 if conf_value > 1.0 else float(conf_value)
        normalized["confidence_score"]["explanation"] = llm_output.get("confidence_explanation", "Based on data availability and source reliability")
    
    # Ensure all fields are the correct type
    if not isinstance(normalized["core_findings"]["summary"], list):
        normalized["core_findings"]["summary"] = []
    if not isinstance(normalized["core_findings"]["detailed_points"], list):
        normalized["core_findings"]["detailed_points"] = []
    if not isinstance(normalized["tables"], list):
        normalized["tables"] = []
    if not isinstance(normalized["key_insights"], list):
        normalized["key_insights"] = []
    if not isinstance(normalized["timeline"], list):
        normalized["timeline"] = []
    if not isinstance(normalized["citations"], list):
        normalized["citations"] = []
    
    return normalized


def get_unified_schema_prompt(agent_name: str) -> str:
    """Get the unified schema prompt instruction for LLM."""
    return f"""
CRITICAL INSTRUCTIONS:
- You are a pharmaceutical research AI agent
- You MUST respond with ONLY valid JSON - NO other text before or after
- Do NOT use markdown code blocks (no ``` or ```json)
- Start your response with {{ and end with }}
- Every field must be present in the JSON

MANDATORY JSON SCHEMA:
{{
  "agent_name": "{agent_name}",
  "agent_version": "1.0",
  "query_understanding": {{
    "original_query": "the user's original query",
    "intent": "what the user is trying to understand",
    "subtasks": ["subtask 1", "subtask 2"]
  }},
  "core_findings": {{
    "summary": ["bullet point 1", "bullet point 2", "bullet point 3"],
    "detailed_points": ["detailed insight 1", "detailed insight 2"]
  }},
  "tables": [
    {{
      "title": "Table Title",
      "columns": ["Column 1", "Column 2", "Column 3"],
      "rows": [
        ["value 1", "value 2", "value 3"],
        ["value 4", "value 5", "value 6"]
      ],
      "interpretation": "What this table means and why it matters"
    }}
  ],
  "key_insights": [
    {{
      "category": "market | clinical | patent | trial | regulatory | safety | efficacy | competition | supply-chain | mechanism",
      "insight": "the key finding",
      "explanation": "what this means",
      "implication": "why this matters for drug development"
    }}
  ],
  "timeline": [
    {{
      "step": "milestone name",
      "description": "what happened or will happen",
      "status": "pending | complete | in-progress"
    }}
  ],
  "citations": [
    {{
      "source": "source name",
      "url": "URL if available",
      "type": "clinical_trial | publication | guideline | patent | database | news",
      "quote": "relevant quote or excerpt"
    }}
  ],
  "confidence_score": {{
    "value": 0.85,
    "explanation": "why this confidence level (based on data availability, source reliability, etc.)"
  }}
}}

RULES:
1. Start response with {{ - no text before the JSON
2. ALL fields MUST be present (use empty arrays [] or empty strings "" if no data)
3. core_findings.summary must have 3-5 bullet points
4. End response with }} - no text after the JSON
5. NO markdown formatting - just pure JSON
3. confidence_score.value must be between 0.0 and 1.0
4. Every insight MUST include explanation and implication
5. Every table MUST include interpretation
6. Return ONLY the JSON object, nothing else
"""

