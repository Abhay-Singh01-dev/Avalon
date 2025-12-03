"""
MODE ENGINE TEST PROMPTS
========================

Copy these prompts into the chat interface to test each mode of the Mode Engine.
Expected mode is shown in brackets.

"""

# ============================================================================
# SAFETY MODE TESTS (Non-Pharma Queries - Should be blocked)
# ============================================================================

SAFETY_MODE_PROMPTS = [
    "How do I fix this React error?",
    "What's the weather forecast for tomorrow?",
    "Write a Python function to reverse a string",
    "Best Italian restaurants in Manhattan",
    "How to invest in Bitcoin?",
    "Explain the plot of The Matrix",
    "What are the tax implications of crypto trading?",
    "How do I center a div in CSS?",
]

# ============================================================================
# TABLE MODE TESTS (Should generate clean Markdown tables)
# ============================================================================

TABLE_MODE_PROMPTS = [
    "Give me a table of top 5 diabetes drugs with their mechanisms",
    "Create a comparison table of GLP-1 agonists",
    "Make a simple table showing statins with dosage and side effects",
    "Show me an overview table of chemotherapy drugs for breast cancer",
    "Create a 2-column table with drug names and their primary indications",
    "Format a table comparing insulin types: rapid-acting vs long-acting",
    "Give me a compact table of beta blockers with their selectivity",
    "Make a tabular comparison of NSAIDs",
]

# ============================================================================
# SIMPLE MODE TESTS (Should get quick, concise answers)
# ============================================================================

SIMPLE_MODE_PROMPTS = [
    "What are the side effects of aspirin?",
    "List the indications for metformin",
    "Explain the MOA of ibuprofen",
    "What is warfarin used for?",
    "Brief overview of insulin types",
    "Quick summary of statins",
    "Define pharmacokinetics",
    "Explain how ACE inhibitors work",
    "What is the half-life of metformin?",
    "List contraindications for warfarin",
]

# ============================================================================
# RESEARCH MODE TESTS (Should trigger full multi-agent orchestration)
# ============================================================================

RESEARCH_MODE_PROMPTS = [
    "Analyze the market landscape for minocycline in Parkinson's disease",
    "Deep dive into clinical trial evidence for adalimumab biosimilars",
    "Comprehensive SWOT analysis of metformin repurposing in oncology",
    "Identify patent opportunities for tocilizumab in rare diseases",
    "Full regulatory pathway analysis for new GLP-1 drugs in the US",
    "Unmet needs analysis in the Alzheimer's therapeutic space",
    "Competitive landscape and pipeline for NASH treatments",
    "Detailed market analysis of diabetes drug market with growth projections",
]

# ============================================================================
# DOCUMENT MODE TESTS (File-based - requires file upload)
# ============================================================================

DOCUMENT_MODE_PROMPTS = [
    "Analyze this clinical trial document",
    "Summarize the key findings from this PDF",
    "Extract the efficacy data from this research paper",
    "What does this study say about adverse events?",
    "Give me a summary of the methods section in this document",
]

# ============================================================================
# EDGE CASES (Test boundary conditions)
# ============================================================================

EDGE_CASE_PROMPTS = [
    # Should be TABLE (not RESEARCH despite "analysis")
    "Create a table for market analysis of top 5 diabetes drugs",
    
    # Should be SIMPLE (short pharma query)
    "What is metformin?",
    
    # Should be RESEARCH (contains research keyword)
    "Analyze diabetes market trends",
    
    # Should be TABLE (table keyword overrides simple)
    "Brief overview table of insulin types",
    
    # Should be SIMPLE (despite mentioning drugs)
    "Aspirin side effects",
    
    # Should be RESEARCH (deep analysis requested)
    "Give me a comprehensive analysis of aspirin usage patterns",
]

# ============================================================================
# PRINT ALL PROMPTS FOR EASY COPY-PASTE
# ============================================================================

def print_all_prompts():
    print("\n" + "="*80)
    print("MODE ENGINE TEST PROMPTS - Copy & Paste Into Chat")
    print("="*80 + "\n")
    
    print("🛡️  SAFETY MODE (Should block non-pharma queries)")
    print("-" * 80)
    for i, prompt in enumerate(SAFETY_MODE_PROMPTS, 1):
        print(f"{i}. {prompt}")
    
    print("\n📊 TABLE MODE (Should generate clean Markdown tables)")
    print("-" * 80)
    for i, prompt in enumerate(TABLE_MODE_PROMPTS, 1):
        print(f"{i}. {prompt}")
    
    print("\n⚡ SIMPLE MODE (Should get quick answers without agents)")
    print("-" * 80)
    for i, prompt in enumerate(SIMPLE_MODE_PROMPTS, 1):
        print(f"{i}. {prompt}")
    
    print("\n🔬 RESEARCH MODE (Should trigger full multi-agent pipeline)")
    print("-" * 80)
    for i, prompt in enumerate(RESEARCH_MODE_PROMPTS, 1):
        print(f"{i}. {prompt}")
    
    print("\n📄 DOCUMENT MODE (File-based - requires upload)")
    print("-" * 80)
    for i, prompt in enumerate(DOCUMENT_MODE_PROMPTS, 1):
        print(f"{i}. {prompt}")
    
    print("\n🎯 EDGE CASES (Test boundary conditions)")
    print("-" * 80)
    for i, prompt in enumerate(EDGE_CASE_PROMPTS, 1):
        print(f"{i}. {prompt}")
    
    print("\n" + "="*80)
    print("TESTING TIPS:")
    print("="*80)
    print("✓ Watch for thinking animation (should appear in all modes except SAFETY)")
    print("✓ Check response format (tables should have pipes and separators)")
    print("✓ Verify timeline events appear ONLY in RESEARCH mode")
    print("✓ Simple mode should respond in under 10 seconds")
    print("✓ Safety mode should respond instantly (<1 second)")
    print("✓ Table mode should produce ONLY a table, no extra text")
    print("="*80 + "\n")


if __name__ == "__main__":
    print_all_prompts()
