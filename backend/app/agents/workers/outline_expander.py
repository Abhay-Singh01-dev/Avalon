"""
Two-step outline-then-expand approach for worker agents.
Optimized for small models like Mistral-7B.
"""
from typing import Dict, Any, List
import json
import re
from app.llm.lmstudio_client import lmstudio_client
from app.config import settings
from app.core.cache import cache, CacheManager
from app.core.logger import get_logger

logger = get_logger(__name__)


async def generate_outline(query: str, agent_type: str, cache_prefix: str = "outline") -> List[str]:
    """
    STEP 1: Generate a structured outline (bullet points only, no prose).
    This is easy even for small models like Mistral-7B.
    """
    # Check cache first
    cache_key = CacheManager.make_key({
        "type": cache_prefix,
        "agent": agent_type,
        "query": query
    })
    
    try:
        cached_outline = cache.get(cache_key, default=None)
        if cached_outline is not None:
            logger.info(f"Outline cache hit for {agent_type}")
            return cached_outline
    except Exception:
        pass
    
    outline_prompt = f"""Generate a structured outline for answering this pharmaceutical research question.

Question: {query}

Requirements:
1. Bullet points ONLY
2. NO prose or full sentences
3. NO generic filler like "market is growing"
4. Each point must be specific and factual
5. Focus on concrete data points and insights
6. Maximum 8-10 bullet points

Format:
- Point 1: [specific topic]
- Point 2: [specific topic]
- Point 3: [specific topic]
...

Generate the outline now:"""

    try:
        raw_outline = await lmstudio_client.ask_llm(
            [{"role": "user", "content": outline_prompt}],
            model=settings.LMSTUDIO_MODEL_NAME
        )
        
        # Extract bullet points
        lines = raw_outline.strip().split('\n')
        outline_points = []
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                # Remove bullet markers
                point = re.sub(r'^[-•*]\s*', '', line).strip()
                if point and len(point) > 10:  # Skip very short points
                    outline_points.append(point)
        
        # Cache the outline
        try:
            cache.set(cache_key, outline_points)
        except Exception:
            pass
        
        logger.info(f"Generated {len(outline_points)} outline points for {agent_type}")
        return outline_points
    
    except Exception as e:
        logger.error(f"Outline generation failed: {e}")
        return []


async def expand_outline_points(
    outline_points: List[str],
    query: str,
    agent_type: str,
    agent_persona: str
) -> Dict[str, Any]:
    """
    STEP 2: Expand each outline point one by one.
    Uses verification scaffold for quality control.
    """
    expanded_sections = []
    seen_sentences = set()  # Track to avoid repetition
    
    for idx, point in enumerate(outline_points, 1):
        expansion_prompt = f"""{agent_persona}

Original Question: {query}

Current Section to Expand: {point}

Previous sections covered: {', '.join([p[:50] + '...' for p in outline_points[:idx-1]])}

VERIFICATION SCAFFOLD:
Expand this section using THREE levels of certainty:

1. CERTAIN FACTS (High Confidence):
   - What I can confirm with high certainty
   - Specific data points, mechanisms, or findings
   - 2-3 sentences maximum

2. LIKELY BUT NOT CERTAIN (Medium Confidence):
   - What is probable based on available evidence
   - Trends or patterns that need qualification
   - 2-3 sentences maximum

3. UNCERTAIN OR CANNOT ANSWER (Low Confidence):
   - What requires more data
   - What is speculative
   - 1-2 sentences maximum

CRITICAL RULES:
- Keep each section 50-80 tokens
- NO generic filler like "market is growing"
- NO repetition of previous sections
- NO marketing-style language
- NO repeated mechanistic explanations
- Be SPECIFIC with numbers, dates, compounds
- Use technical precision

Expand section {idx} now:"""

        try:
            expansion = await lmstudio_client.ask_llm(
                [{"role": "user", "content": expansion_prompt}],
                model=settings.LMSTUDIO_MODEL_NAME
            )
            
            # Filter out repeated sentences
            filtered_expansion = filter_repetitions(expansion, seen_sentences)
            
            if filtered_expansion:
                expanded_sections.append({
                    "section": point,
                    "content": filtered_expansion,
                    "index": idx
                })
                
                # Add new sentences to seen set
                for sentence in filtered_expansion.split('.'):
                    if len(sentence.strip()) > 20:
                        seen_sentences.add(sentence.strip().lower())
        
        except Exception as e:
            logger.error(f"Failed to expand point {idx}: {e}")
            continue
    
    return {
        "outline": outline_points,
        "expanded_sections": expanded_sections,
        "total_sections": len(expanded_sections)
    }


def filter_repetitions(text: str, seen_sentences: set) -> str:
    """
    Remove repeated sentences and generic filler.
    """
    # Generic filler phrases to remove
    filler_phrases = [
        "the market is growing",
        "this is an important area",
        "further research is needed",
        "it is widely known",
        "studies have shown",
        "it is important to note",
        "this demonstrates that",
        "as mentioned earlier",
        "as discussed above",
        "in summary",
        "in conclusion"
    ]
    
    sentences = text.split('.')
    filtered_sentences = []
    
    for sentence in sentences:
        sentence_clean = sentence.strip().lower()
        
        # Skip empty sentences
        if len(sentence_clean) < 20:
            continue
        
        # Skip generic filler
        if any(filler in sentence_clean for filler in filler_phrases):
            continue
        
        # Skip if we've seen this sentence before
        if sentence_clean in seen_sentences:
            continue
        
        # Skip if it's too similar to existing sentences
        is_duplicate = False
        for seen in seen_sentences:
            if len(seen) > 30 and len(sentence_clean) > 30:
                # Check for high similarity (simple word overlap)
                seen_words = set(seen.split())
                current_words = set(sentence_clean.split())
                overlap = len(seen_words & current_words) / max(len(seen_words), len(current_words))
                if overlap > 0.7:  # 70% word overlap = likely duplicate
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            filtered_sentences.append(sentence.strip())
    
    return '. '.join(filtered_sentences) + '.' if filtered_sentences else ""


def clean_meta_text(text: str) -> str:
    """
    Remove ALL meta-text, labels, and scaffold markers from output.
    STRICT MODE: Output ONLY factual content.
    """
    # Remove verification scaffold labels
    patterns = [
        r'CERTAIN FACTS?:?\s*\(?High Confidence\)?:?',
        r'LIKELY BUT NOT CERTAIN:?\s*\(?Medium Confidence\)?:?',
        r'UNCERTAIN OR CANNOT ANSWER:?\s*\(?Low Confidence\)?:?',
        r'High Confidence:?',
        r'Medium Confidence:?',
        r'Low Confidence:?',
        r'What (I|we) can confirm with high certainty:?',
        r'What is probable based on available evidence:?',
        r'What requires more data:?',
        r'Current Section to Expand:?',
        r'Original Question:?',
        r'Previous sections covered:?',
        r'\d+\.\s*(CERTAIN|LIKELY|UNCERTAIN)',
    ]
    
    cleaned = text
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # DO NOT remove numbered list markers - preserve list formatting
    # Only clean up extra whitespace while preserving list structure
    
    # Clean up extra whitespace but preserve list formatting with proper spacing
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
                cleaned_lines.append("")
                prev_was_empty = True
            elif prev_was_list and not prev_was_empty:
                cleaned_lines.append("")
                prev_was_empty = True
            prev_was_list = False
            prev_was_paragraph = False
        elif is_list_item:
            # List item - ensure proper spacing before first list item only
            # Do NOT add blank lines between consecutive list items
            if not prev_was_list and not prev_was_empty and i > 0:
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
            cleaned_line = re.sub(r'  +', ' ', line_stripped)
            if cleaned_line:
                # Add blank line before paragraph if previous was a list
                if prev_was_list and not prev_was_empty:
                    cleaned_lines.append("")
                cleaned_lines.append(cleaned_line)
                prev_was_paragraph = True
                prev_was_list = False
                prev_was_empty = False
    
    cleaned = '\n'.join(cleaned_lines)
    
    # Replace 3+ consecutive newlines with double newline (normal paragraph spacing)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    return cleaned.strip()


def merge_and_format_sections(expanded_sections: List[Dict[str, Any]], agent_name: str, strict_mode: bool = True) -> str:
    """
    Merge expanded sections into clean output format.
    STRICT MODE: Remove headings, meta-text, and agent names. Output ONLY the content.
    """
    if not expanded_sections:
        return ""
    
    # STRICT OUTPUT MODE: No headings, no meta-text, just clean content
    formatted_output = []
    all_sentences = set()
    
    for section in expanded_sections:
        section_content = section.get("content", "")
        
        # Filter duplicates across all sections
        filtered_content = filter_repetitions(section_content, all_sentences)
        
        if filtered_content:
            if strict_mode:
                # STRICT MODE: Clean ALL meta-text and output ONLY content
                cleaned_content = clean_meta_text(filtered_content)
                if cleaned_content:
                    # Add blank line before new section if not first section
                    if formatted_output:
                        formatted_output.append("")
                    formatted_output.append(cleaned_content)
            else:
                # Legacy mode: Include section headings
                section_title = section.get("section", "").split(':')[0].strip()
                if formatted_output:
                    formatted_output.append("")
                formatted_output.append(f"## {section_title}")
                formatted_output.append(filtered_content)
            
            # Add sentences to global seen set
            for sentence in filtered_content.split('.'):
                if len(sentence.strip()) > 20:
                    all_sentences.add(sentence.strip().lower())
    
    return '\n'.join(formatted_output)


def extract_key_insights(expanded_sections: List[Dict[str, Any]]) -> List[str]:
    """
    Extract key insights from expanded sections.
    Focus on high-certainty facts.
    STRICT MODE: Remove ALL meta-text labels.
    """
    insights = []
    
    for section in expanded_sections:
        content = section.get("content", "")
        
        # Look for sentences with certainty markers
        certainty_markers = [
            "CERTAIN FACTS:",
            "High Confidence:",
            "confirmed",
            "demonstrated",
            "established"
        ]
        
        sentences = content.split('.')
        for sentence in sentences:
            sentence_clean = sentence.strip()
            if len(sentence_clean) > 30:  # Skip very short sentences
                # Check if it contains certainty markers or specific data
                has_certainty = any(marker.lower() in sentence_clean.lower() for marker in certainty_markers)
                has_numbers = bool(re.search(r'\d+', sentence_clean))
                
                if has_certainty or has_numbers:
                    # STRICT MODE: Remove ALL meta-text labels and scaffold markers
                    factual_part = re.sub(r'(CERTAIN FACTS?:|High Confidence?:|LIKELY BUT NOT CERTAIN:|Medium Confidence?:|UNCERTAIN OR CANNOT ANSWER:|Low Confidence?:|\d+\.\s*)', '', sentence_clean, flags=re.IGNORECASE).strip()
                    # Remove common meta-text patterns
                    factual_part = re.sub(r'^(What (I|we) can confirm|What is probable|What requires)', '', factual_part, flags=re.IGNORECASE).strip()
                    if factual_part and len(factual_part) > 20:
                        insights.append(factual_part)
    
    # Return top 10 most substantial insights
    return sorted(insights, key=len, reverse=True)[:10]
