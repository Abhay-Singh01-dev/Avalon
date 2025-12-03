"""
Test the simple query bypass functionality.

This test verifies that basic queries (tables, lists, MOA, side effects)
bypass the multi-agent pharma research mode and go directly to the LLM.
"""

def test_simple_keyword_detection():
    """Test that simple query keywords are properly detected"""
    
    simple_keywords = [
        "table", "simple table", "overview table", "small table", "compact table",
        "list", "high-level", "brief", "short", "quick",
        "mechanism", "moa", "mechanism of action",
        "side effects", "adverse effects", "adverse events",
        "basic explanation", "simple explanation", "overview", "summary"
    ]
    
    # Test queries that SHOULD trigger bypass
    bypass_queries = [
        "Give me a table of top 5 diabetes drugs",
        "List the side effects of aspirin",
        "What is the mechanism of action of metformin?",
        "Brief overview of GLP-1 agonists",
        "Create a simple table comparing statins",
        "What are the adverse effects of warfarin?",
        "Quick summary of insulin types",
        "Compact table of chemotherapy drugs",
        "High-level overview of cancer immunotherapy",
        "Short explanation of MOA for ibuprofen"
    ]
    
    # Test queries that should NOT trigger bypass (complex pharma queries)
    no_bypass_queries = [
        "Analyze the market landscape for minocycline in Parkinson's disease",
        "Find patent opportunities for tocilizumab repurposing",
        "Deep dive into clinical trial evidence for adalimumab biosimilars",
        "Comprehensive SWOT analysis of metformin in oncology",
        "Identify emerging competition in the diabetes space"
    ]
    
    print("Testing BYPASS queries (should detect simple keywords):")
    for query in bypass_queries:
        query_lower = query.lower()
        is_simple = any(keyword in query_lower for keyword in simple_keywords)
        status = "✅ BYPASS" if is_simple else "❌ FAILED (should bypass)"
        print(f"{status}: {query}")
    
    print("\n" + "="*80 + "\n")
    print("Testing COMPLEX queries (should NOT bypass):")
    for query in no_bypass_queries:
        query_lower = query.lower()
        is_simple = any(keyword in query_lower for keyword in simple_keywords)
        status = "✅ NO BYPASS" if not is_simple else "❌ FAILED (should not bypass)"
        print(f"{status}: {query}")


if __name__ == "__main__":
    test_simple_keyword_detection()
