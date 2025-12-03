"""
Test the Mode Engine functionality.

This test verifies that the Mode Engine correctly detects and routes
queries to the appropriate mode: SAFETY, DOCUMENT, TABLE, SIMPLE, or RESEARCH.
"""

from app.routes.chat import detect_mode, ChatMode


def test_safety_mode_detection():
    """Test SAFETY mode for non-pharma queries"""
    print("="*80)
    print("TESTING SAFETY MODE (Non-Pharma Queries)")
    print("="*80)
    
    safety_queries = [
        "How do I fix a JavaScript error?",
        "What's the weather today?",
        "Tell me about the latest Marvel movie",
        "How to invest in cryptocurrency?",
        "Write a Python function to sort an array",
        "What's the capital of France?",
        "Explain quantum mechanics",
        "Best restaurants in New York"
    ]
    
    for query in safety_queries:
        mode = detect_mode(query, has_files=False)
        status = "✅" if mode == ChatMode.SAFETY else f"❌ (got {mode})"
        print(f"{status} {query}")
    
    print()


def test_table_mode_detection():
    """Test TABLE mode for table generation requests"""
    print("="*80)
    print("TESTING TABLE MODE (Table Requests)")
    print("="*80)
    
    table_queries = [
        "Give me a table of top diabetes drugs",
        "Create a comparison table of statins",
        "Make a simple table showing GLP-1 agonists",
        "Convert this to tabular form",
        "Show me an overview table of chemotherapy drugs",
        "Create a 2-column table with drug names and indications",
        "Format this as a table with columns for drug, dose, and route"
    ]
    
    for query in table_queries:
        mode = detect_mode(query, has_files=False)
        status = "✅" if mode == ChatMode.TABLE else f"❌ (got {mode})"
        print(f"{status} {query}")
    
    print()


def test_simple_mode_detection():
    """Test SIMPLE mode for quick informational queries"""
    print("="*80)
    print("TESTING SIMPLE MODE (Quick Info Queries)")
    print("="*80)
    
    simple_queries = [
        "What are the side effects of aspirin?",
        "List the indications for metformin",
        "Explain the MOA of ibuprofen",
        "Brief overview of insulin types",
        "What is adalimumab used for?",
        "Quick summary of statins",
        "Define pharmacokinetics",
        "Explain briefly how warfarin works"
    ]
    
    for query in simple_queries:
        mode = detect_mode(query, has_files=False)
        status = "✅" if mode == ChatMode.SIMPLE else f"❌ (got {mode})"
        print(f"{status} {query}")
    
    print()


def test_research_mode_detection():
    """Test RESEARCH mode for deep pharma research queries"""
    print("="*80)
    print("TESTING RESEARCH MODE (Deep Research)")
    print("="*80)
    
    research_queries = [
        "Analyze the market landscape for minocycline in Parkinson's disease",
        "Deep dive into clinical trial evidence for adalimumab biosimilars",
        "Comprehensive SWOT analysis of metformin in oncology",
        "Identify patent opportunities for tocilizumab repurposing",
        "Full regulatory pathway analysis for new diabetes drugs",
        "Unmet needs analysis in the oncology space",
        "Competitive landscape for GLP-1 receptor agonists",
        "Detailed pipeline analysis for Alzheimer's therapeutics"
    ]
    
    for query in research_queries:
        mode = detect_mode(query, has_files=False)
        status = "✅" if mode == ChatMode.RESEARCH else f"❌ (got {mode})"
        print(f"{status} {query}")
    
    print()


def test_document_mode_detection():
    """Test DOCUMENT mode for file-based queries"""
    print("="*80)
    print("TESTING DOCUMENT MODE (File-Based)")
    print("="*80)
    
    document_queries = [
        ("Analyze this clinical trial document", False),
        ("Summarize this pdf about diabetes drugs", False),
        ("Extract data from the uploaded file", False),
        ("Read the document and give me key findings", False),
        ("What does this research paper say?", True),  # has_files=True
    ]
    
    for query, has_files in document_queries:
        mode = detect_mode(query, has_files=has_files)
        expected = ChatMode.DOCUMENT
        status = "✅" if mode == expected else f"❌ (got {mode})"
        files_note = " [with files]" if has_files else ""
        print(f"{status} {query}{files_note}")
    
    print()


def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("="*80)
    print("TESTING EDGE CASES")
    print("="*80)
    
    edge_cases = [
        # Should be TABLE (not RESEARCH despite "analysis")
        ("Create a table for market analysis of diabetes drugs", ChatMode.TABLE),
        
        # Should be SIMPLE (despite containing "drug")
        ("What is metformin?", ChatMode.SIMPLE),
        
        # Should be RESEARCH (despite being short, contains research keyword)
        ("Analyze diabetes market", ChatMode.RESEARCH),
        
        # Should be SIMPLE (short pharma query)
        ("Aspirin side effects", ChatMode.SIMPLE),
        
        # Should be TABLE (contains table keyword)
        ("Brief overview table of insulin types", ChatMode.TABLE),
    ]
    
    for query, expected_mode in edge_cases:
        mode = detect_mode(query, has_files=False)
        status = "✅" if mode == expected_mode else f"❌ (got {mode}, expected {expected_mode})"
        print(f"{status} {query}")
    
    print()


def run_all_tests():
    """Run all Mode Engine tests"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "MODE ENGINE TEST SUITE" + " "*37 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    test_safety_mode_detection()
    test_table_mode_detection()
    test_simple_mode_detection()
    test_research_mode_detection()
    test_document_mode_detection()
    test_edge_cases()
    
    print("="*80)
    print("✅ MODE ENGINE TESTS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    run_all_tests()
