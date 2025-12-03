"""
Table Formatting Utility - STRICT Small-LLM-Friendly Markdown Tables

This module enforces strict table formatting rules for small LLMs (like Mistral-7B)
that struggle with table generation.

STRICT RULES:
1. Every table: | Column | Column | Column | format
2. NO multiline cells - max 10 words per cell
3. NO line breaks inside cells
4. SHORT phrases only
5. Auto-compress verbose content
6. Fallback sanity check for malformed tables

Small-LLM Optimizations:
- Compress long sentences into 3-6 word phrases
- Remove line breaks and wrapping
- Enforce equal column counts
- Clean whitespace aggressively
- Reformat broken tables automatically
"""

import logging
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def _compress_cell_content(text: str, max_words: int = 10) -> str:
    """
    Compress cell content to SHORT phrases (max 10 words).
    Removes line breaks, trims sentences, keeps it concise.
    
    Args:
        text: Original cell text
        max_words: Maximum words per cell (default: 10)
    
    Returns:
        str: Compressed cell content
    """
    if not text or not isinstance(text, str):
        return "Unknown"
    
    # Remove all line breaks and excessive whitespace
    text = re.sub(r'[\n\r\t]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Remove markdown formatting
    text = re.sub(r'[*_~`#]', '', text)
    
    # Split into words
    words = text.split()
    
    # If exceeds max_words, truncate intelligently
    if len(words) > max_words:
        # Try to keep first complete phrase
        truncated = ' '.join(words[:max_words])
        # Remove trailing punctuation if cut mid-sentence
        truncated = truncated.rstrip('.,;:')
        return truncated
    
    return text


def format_table(
    rows: List[Dict[str, Any]],
    headers: Optional[List[str]] = None,
    max_rows: int = 6,
    max_cols: int = 3,
    fill_empty: str = "Unknown"
) -> str:
    """
    Format data into STRICT small-LLM-friendly Markdown table.
    
    ENFORCES:
    - Max 10 words per cell
    - NO line breaks inside cells
    - SHORT phrases only
    - Clean whitespace
    - Equal column counts
    
    Args:
        rows: List of dictionaries representing table rows
        headers: Optional list of column headers (auto-detected if not provided)
        max_rows: Maximum number of rows (default: 6)
        max_cols: Maximum number of columns (default: 3)
        fill_empty: Value to use for empty cells (default: "Unknown")
    
    Returns:
        str: Formatted Markdown table with strict formatting
    """
    if not rows:
        return _get_empty_table_fallback()
    
    # Auto-detect headers if not provided
    if headers is None:
        headers = list(rows[0].keys())
    
    # Limit columns
    headers = headers[:max_cols]
    
    # Compress header names
    headers = [_compress_cell_content(h, max_words=3) for h in headers]
    
    # Limit rows
    rows = rows[:max_rows]
    
    # Build table
    table_lines = []
    
    # Header row
    header_row = "| " + " | ".join(headers) + " |"
    table_lines.append(header_row)
    
    # Separator row
    separator = "|" + "|".join([" ---------- " for _ in headers]) + "|"
    table_lines.append(separator)
    
    # Data rows
    for row in rows:
        cells = []
        for header_original in list(rows[0].keys())[:max_cols]:
            value = row.get(header_original, fill_empty)
            
            # Handle None, empty strings, or whitespace-only values
            if value is None or (isinstance(value, str) and not value.strip()):
                value = fill_empty
            
            # Convert to string and compress
            value_str = str(value).strip()
            
            # CRITICAL: Compress to max 10 words
            value_str = _compress_cell_content(value_str, max_words=10)
            
            # Escape pipe characters
            value_str = value_str.replace("|", "\\|")
            
            cells.append(value_str)
        
        data_row = "| " + " | ".join(cells) + " |"
        table_lines.append(data_row)
    
    return "\n".join(table_lines)


def extract_table_from_text(text: str) -> Optional[str]:
    """
    Extract and validate Markdown table from LLM response.
    Handles multiline cells by merging them back together.
    
    Args:
        text: LLM response text that may contain a table
    
    Returns:
        str: Validated table if found, None otherwise
    """
    lines = text.split("\n")
    
    table_lines = []
    in_table = False
    current_row = ""
    
    for line in lines:
        stripped = line.strip()
        
        # Detect table start or continuation
        if stripped.startswith("|") and "|" in stripped[1:]:
            if not in_table:
                in_table = True
            
            # Check if this might be a continuation (no proper pipe structure)
            pipe_count = stripped.count("|")
            
            if pipe_count >= 3:  # Proper table row (at least 2 columns)
                # Save previous row if exists
                if current_row:
                    table_lines.append(current_row)
                current_row = line
            else:
                # Might be continuation of previous row
                if current_row:
                    current_row += " " + stripped.strip("|").strip()
                else:
                    current_row = line
        elif in_table:
            if stripped and not stripped.startswith("|"):
                # Check if this is text continuation inside a cell
                if current_row and not re.match(r'^\|\s*[-:]+\s*\|', current_row):
                    # Merge into current row
                    current_row += " " + stripped
                else:
                    # End of table
                    if current_row:
                        table_lines.append(current_row)
                    break
    
    # Add last row if exists
    if current_row and in_table:
        table_lines.append(current_row)
    
    if len(table_lines) < 3:  # Need at least header, separator, and one data row
        return None
    
    return "\n".join(table_lines)


def validate_and_fix_table(table_text: str, max_cols: int = 3) -> str:
    """
    FALLBACK SANITY CHECK: Validate and aggressively fix malformed tables.
    
    Fixes:
    - Cleans whitespace
    - Reformats rows
    - Enforces equal column counts
    - Strips sentences > 10 words per cell
    - Removes line breaks
    - Regenerates table cleanly
    
    Args:
        table_text: Raw table text from LLM
        max_cols: Maximum columns to keep
    
    Returns:
        str: Fixed and validated table with strict formatting
    """
    lines = table_text.strip().split("\n")
    
    if len(lines) < 3:
        return _get_empty_table_fallback()
    
    # Process lines
    fixed_lines = []
    expected_cols = max_cols
    
    for i, line in enumerate(lines):
        # Remove excessive whitespace
        line = re.sub(r'\s+', ' ', line.strip())
        
        # Split by pipes
        parts = [p.strip() for p in line.split("|")]
        
        # Remove empty first/last elements (from leading/trailing pipes)
        if parts and not parts[0]:
            parts = parts[1:]
        if parts and not parts[-1]:
            parts = parts[:-1]
        
        # Clean each cell
        cleaned_parts = []
        for part in parts:
            # Remove line breaks inside cells
            part = re.sub(r'[\n\r]+', ' ', part)
            part = re.sub(r'\s+', ' ', part)
            
            # Compress if too long (max 10 words)
            part = _compress_cell_content(part, max_words=10)
            
            cleaned_parts.append(part)
        
        # Detect expected columns from first row
        if i == 0:
            expected_cols = min(len(cleaned_parts), max_cols)
        
        # Limit columns to expected count
        cleaned_parts = cleaned_parts[:expected_cols]
        
        # Fill missing columns
        while len(cleaned_parts) < expected_cols:
            cleaned_parts.append("Unknown")
        
        # Rebuild line
        if i == 1:  # Separator row
            fixed_line = "|" + "|".join([" ---------- " for _ in range(expected_cols)]) + "|"
        else:
            fixed_line = "| " + " | ".join(cleaned_parts) + " |"
        
        fixed_lines.append(fixed_line)
    
    # Ensure separator exists
    if len(fixed_lines) >= 2 and not re.match(r'^\|\s*[-:]+\s*\|', fixed_lines[1]):
        # Insert proper separator after header
        separator = "|" + "|".join([" ---------- " for _ in range(expected_cols)]) + "|"
        fixed_lines.insert(1, separator)
    
    return "\n".join(fixed_lines)


def _get_empty_table_fallback() -> str:
    """
    Generate a fallback table when data is unavailable.
    
    Returns:
        str: Minimal fallback table
    """
    return """| Item | Details | Status |
| --- | --- | --- |
| Data | Not available | Unknown |"""


def enforce_table_quality(llm_response: str, prompt: str) -> str:
    """
    Enforce table quality standards on LLM response.
    
    If LLM struggles with table generation:
    1. Extract any existing table
    2. Validate and fix structure
    3. Generate fallback if needed
    
    Args:
        llm_response: Raw LLM response
        prompt: Original user prompt
    
    Returns:
        str: Response with guaranteed quality table
    """
    # Try to extract table from response
    table = extract_table_from_text(llm_response)
    
    if table:
        # Validate and fix
        fixed_table = validate_and_fix_table(table, max_cols=3)
        
        # Replace in response
        return llm_response.replace(table, fixed_table)
    
    # No table found - check if one was requested
    if any(kw in prompt.lower() for kw in ["table", "tabular", "compare"]):
        logger.warning("Table requested but not found in LLM response - generating fallback")
        
        # Add fallback table
        fallback = f"\n\n{_get_empty_table_fallback()}\n\n*Note: Unable to generate detailed table. Please refine your query.*"
        return llm_response + fallback
    
    return llm_response


def create_comparison_table(
    items: List[str],
    attributes: List[str],
    data: Dict[str, Dict[str, Any]]
) -> str:
    """
    Create a comparison table from structured data.
    
    Args:
        items: List of items to compare (e.g., drug names)
        attributes: List of attributes to show (e.g., "MOA", "Indications")
        data: Nested dict with item -> attribute -> value mappings
    
    Returns:
        str: Formatted comparison table
    
    Example:
        items = ["Metformin", "Glipizide"]
        attributes = ["Class", "MOA", "Side Effects"]
        data = {
            "Metformin": {"Class": "Biguanide", "MOA": "...", ...},
            "Glipizide": {"Class": "Sulfonylurea", "MOA": "...", ...}
        }
    """
    # Limit items and attributes for readability
    items = items[:6]  # Max 6 items
    attributes = attributes[:3]  # Max 3 attributes
    
    # Build rows
    rows = []
    
    for item in items:
        row = {"Item": item}
        
        for attr in attributes:
            value = data.get(item, {}).get(attr, "Unknown")
            row[attr] = value
        
        rows.append(row)
    
    headers = ["Item"] + attributes
    
    return format_table(rows, headers=headers)


# Strict table formatting rules for small LLMs
STRICT_TABLE_RULES = """
CRITICAL TABLE FORMATTING RULES (MUST FOLLOW):

1. STRICT MARKDOWN FORMAT:
   | Column A | Column B | Column C |
   |----------|----------|----------|
   | value    | value    | value    |

2. NO MULTILINE CELLS:
   - NO line breaks (\\n) inside cells
   - NO text wrapping
   - NO long sentences
   - Use SHORT phrases (max 10 words per cell)

3. COMPRESS CONTENT:
   - Keep cells concise: 3-6 words ideal
   - Remove unnecessary words
   - Use abbreviations when clear (e.g., "MOA" not "Mechanism of Action")
   - Example BAD: "This drug works by inhibiting the reuptake of serotonin in neurons"
   - Example GOOD: "Inhibits serotonin reuptake"

4. TABLE SIZE LIMITS:
   - Maximum 6 rows (excluding header)
   - Maximum 3 columns
   - If more data needed, create multiple focused tables

5. CLEAN FORMATTING:
   - Equal number of columns in every row
   - Proper pipes: | at start, between, and end
   - Separator row: |----------|----------|----------|
   - No mixed paragraphs inside table

6. EXAMPLES OF CORRECT FORMAT:

GOOD TABLE:
| Drug | Class | MOA |
|----------|----------|----------|
| Metformin | Biguanide | Reduces glucose production |
| Glipizide | Sulfonylurea | Increases insulin secretion |

BAD TABLE (DO NOT DO THIS):
| Drug | Class | Mechanism of Action |
|------|-------|---------------------|
| Metformin | Biguanide | This medication works by decreasing
the amount of glucose that is produced by the liver
and also increases insulin sensitivity |

ALWAYS use GOOD format. NEVER use BAD format.
"""

# Strict hallucination rules system prompt addition
HALLUCINATION_RULES = """
STRICT QUALITY RULES:
- Never invent numbers, statistics, or data points
- Never invent company names or drug names not in your training
- Never invent clinical trial IDs or study results
- Never invent patent numbers or regulatory decisions
- If uncertain, clearly state "Unknown — requires validated data"
- Only provide high-level verified facts from training
- Do not extrapolate beyond available information
- When data is missing, explicitly mark as "Data not available"
"""


def add_table_formatting_rules(system_prompt: str) -> str:
    """
    Add STRICT table formatting rules to system prompt for small LLMs.
    
    Critical for Mistral-7B and other small models that struggle with tables.
    
    Args:
        system_prompt: Original system prompt
    
    Returns:
        str: Enhanced prompt with strict table rules
    """
    return f"{system_prompt}\n\n{STRICT_TABLE_RULES}"


def add_hallucination_protection(system_prompt: str) -> str:
    """
    Add strict hallucination rules to system prompt.
    
    Args:
        system_prompt: Original system prompt
    
    Returns:
        str: Enhanced prompt with quality rules
    """
    return f"{system_prompt}\n\n{HALLUCINATION_RULES}"


def clean_llm_table_output(text: str) -> str:
    """
    Aggressively clean and reformat table output from small LLMs.
    
    This is the main entry point for fixing messy LLM-generated tables.
    
    Fixes:
    - Extracts table from response
    - Removes line breaks inside cells
    - Compresses verbose cells to max 10 words
    - Ensures equal column counts
    - Reformats to strict Markdown
    
    Args:
        text: Raw LLM response containing a table
    
    Returns:
        str: Cleaned text with properly formatted table
    """
    # Extract table
    table = extract_table_from_text(text)
    
    if not table:
        return text
    
    # Validate and fix table structure
    fixed_table = validate_and_fix_table(table, max_cols=3)
    
    # Replace original table with fixed version
    cleaned_text = text.replace(table, fixed_table)
    
    return cleaned_text
