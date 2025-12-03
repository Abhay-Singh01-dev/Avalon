"""
Test Suite for Avalon Auto-Mode Intelligence

Validates automatic mode detection without user specifying mode explicitly.
Tests all 7 modes: SIMPLE, RESEARCH, TABLE, DOCUMENT, SAFETY, PATIENT, EXPERT

Run: python tests/test_auto_mode_intelligence.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.llm.mode_classifier import detect_research_mode, ChatMode


def test_auto_mode_detection():
    """Test automatic mode detection without explicit mode specification"""
    
    print("\n" + "="*80)
    print("🎛 AVALON AUTO-MODE INTELLIGENCE TEST SUITE")
    print("="*80 + "\n")
    
    test_cases = [
        # ========================================================================
        # SIMPLE MODE - High-level questions (3-6 bullets)
        # ========================================================================
        {
            "query": "What is aspirin?",
            "expected_mode": ChatMode.SIMPLE,
            "description": "Simple question about a drug"
        },
        {
            "query": "What is the mechanism of action of metformin?",
            "expected_mode": ChatMode.SIMPLE,
            "description": "MoA question"
        },
        {
            "query": "List common side effects of ibuprofen",
            "expected_mode": ChatMode.SIMPLE,
            "description": "List request"
        },
        {
            "query": "Explain what GLP-1 agonists are",
            "expected_mode": ChatMode.SIMPLE,
            "description": "Explanation request"
        },
        
        # ========================================================================
        # TABLE MODE - Auto-detect comparisons (NO "table" keyword needed)
        # ========================================================================
        {
            "query": "Compare metformin vs sitagliptin",
            "expected_mode": ChatMode.TABLE,
            "description": "Compare query (auto-trigger table)"
        },
        {
            "query": "What are the differences between GLP-1 and SGLT2 inhibitors?",
            "expected_mode": ChatMode.TABLE,
            "description": "Differences query (auto-trigger table)"
        },
        {
            "query": "Ozempic versus Mounjaro",
            "expected_mode": ChatMode.TABLE,
            "description": "VS query (auto-trigger table)"
        },
        {
            "query": "Advantages and disadvantages of insulin therapy",
            "expected_mode": ChatMode.TABLE,
            "description": "Pros/cons query (auto-trigger table)"
        },
        {
            "query": "Market landscape of diabetes drugs",
            "expected_mode": ChatMode.TABLE,
            "description": "Market landscape (auto-trigger table)"
        },
        {
            "query": "Compare phase 3 trials for cancer immunotherapy",
            "expected_mode": ChatMode.TABLE,
            "description": "Trial comparison (auto-trigger table)"
        },
        {
            "query": "Drug classes for hypertension",
            "expected_mode": ChatMode.TABLE,
            "description": "Classes query (auto-trigger table)"
        },
        
        # ========================================================================
        # RESEARCH MODE - Deep analysis with multi-agent routing
        # ========================================================================
        {
            "query": "Analyze the diabetes drug market",
            "expected_mode": ChatMode.RESEARCH,
            "description": "Market analysis (triggers MarketAgent)"
        },
        {
            "query": "GLP-1 agonist competitive landscape",
            "expected_mode": ChatMode.RESEARCH,
            "description": "Competitive landscape (deep analysis, not simple table)"
        },
        {
            "query": "Patent expiry timeline for Humira",
            "expected_mode": ChatMode.RESEARCH,
            "description": "Patent query (triggers PatentAgent)"
        },
        {
            "query": "Clinical trials for Alzheimer's disease in phase 2",
            "expected_mode": ChatMode.RESEARCH,
            "description": "Clinical trials (triggers ClinicalTrialsAgent)"
        },
        {
            "query": "Mechanism and PK/PD of semaglutide",
            "expected_mode": ChatMode.RESEARCH,
            "description": "Mechanism query (triggers PKPDAgent)"
        },
        {
            "query": "Regulatory pathway for biosimilars in EU",
            "expected_mode": ChatMode.RESEARCH,
            "description": "Regulatory query (triggers EXIMAgent)"
        },
        {
            "query": "Recent publications on CAR-T therapy",
            "expected_mode": ChatMode.RESEARCH,
            "description": "Publications (triggers WebIntelAgent)"
        },
        {
            "query": "Comprehensive SGLT2 inhibitor landscape with synthesis",
            "expected_mode": ChatMode.RESEARCH,
            "description": "Comprehensive query (deep synthesis)"
        },
        
        # ========================================================================
        # EXPERT MODE - Auto-detect expert network queries
        # ========================================================================
        {
            "query": "Who are the leading experts in oncology immunotherapy?",
            "expected_mode": ChatMode.EXPERT,
            "description": "Expert identification query"
        },
        {
            "query": "Key opinion leaders for diabetes research",
            "expected_mode": ChatMode.EXPERT,
            "description": "KOL query (auto-trigger expert mode)"
        },
        {
            "query": "Who are the top specialists in rare disease drug development?",
            "expected_mode": ChatMode.EXPERT,
            "description": "Specialist search"
        },
        {
            "query": "Collaboration network for gene therapy",
            "expected_mode": ChatMode.EXPERT,
            "description": "Collaboration query"
        },
        {
            "query": "Top thought leaders in cardiovascular medicine",
            "expected_mode": ChatMode.EXPERT,
            "description": "Thought leader query"
        },
        
        # ========================================================================
        # DOCUMENT MODE - PDF/file analysis
        # ========================================================================
        {
            "query": "Summarize the uploaded clinical trial PDF",
            "expected_mode": ChatMode.DOCUMENT,
            "description": "PDF summarization"
        },
        {
            "query": "Extract data from this document",
            "expected_mode": ChatMode.DOCUMENT,
            "description": "Data extraction"
        },
        {
            "query": "Analyze the uploaded file",
            "expected_mode": ChatMode.DOCUMENT,
            "description": "File analysis"
        },
        
        # ========================================================================
        # PATIENT MODE - Patient-specific with PHI
        # ========================================================================
        {
            "query": "My patient has HbA1c 8.9%, should I adjust metformin?",
            "expected_mode": ChatMode.PATIENT,
            "description": "Patient query with measurement"
        },
        {
            "query": "Patient case: 65yo male, blood pressure 160/95 mmHg",
            "expected_mode": ChatMode.PATIENT,
            "description": "Patient case with vitals"
        },
        {
            "query": "Dosage adjustment for patient with renal impairment",
            "expected_mode": ChatMode.PATIENT,
            "description": "Dosing for patient"
        },
        
        # ========================================================================
        # SAFETY MODE - Non-pharma queries (blocked)
        # ========================================================================
        {
            "query": "How do I build a web application?",
            "expected_mode": ChatMode.SAFETY,
            "description": "Non-pharma query (coding)"
        },
        {
            "query": "What are the best movies of 2024?",
            "expected_mode": ChatMode.SAFETY,
            "description": "Non-pharma query (entertainment)"
        },
        {
            "query": "Solve this math problem: 2x + 5 = 15",
            "expected_mode": ChatMode.SAFETY,
            "description": "Non-pharma query (math)"
        },
    ]
    
    # Run tests
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        query = test["query"]
        expected = test["expected_mode"]
        description = test["description"]
        
        # Detect mode
        classification = detect_research_mode(query)
        actual = classification.mode
        
        # Check if correct
        is_correct = actual == expected
        
        if is_correct:
            passed += 1
            status = "✅ PASS"
        else:
            failed += 1
            status = f"❌ FAIL (got {actual})"
        
        print(f"{i}. {status}")
        print(f"   Query: \"{query}\"")
        print(f"   Expected: {expected} | Actual: {actual}")
        print(f"   Description: {description}")
        print(f"   Reason: {classification.reason}")
        
        if classification.required_agents:
            print(f"   Agents: {', '.join(classification.required_agents)}")
        
        print()
    
    # Summary
    print("="*80)
    print(f"📊 TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {len(test_cases)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/len(test_cases)*100):.1f}%")
    print("="*80)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! AUTO-MODE INTELLIGENCE WORKING PERFECTLY! 🎉\n")
    else:
        print(f"\n⚠️  {failed} tests failed. Review mode detection logic.\n")
    
    return failed == 0


def test_agent_auto_selection():
    """Test automatic agent selection based on query keywords"""
    
    print("\n" + "="*80)
    print("🤖 AGENT AUTO-SELECTION TEST")
    print("="*80 + "\n")
    
    test_cases = [
        {
            "query": "Market analysis of GLP-1 drugs",
            "expected_agents": ["MarketAgent"],
            "description": "Market keyword should trigger MarketAgent"
        },
        {
            "query": "Phase 3 clinical trials for diabetes",
            "expected_agents": ["ClinicalTrialsAgent"],
            "description": "Trial keyword should trigger ClinicalTrialsAgent"
        },
        {
            "query": "Patent expiry of Humira",
            "expected_agents": ["PatentAgent"],
            "description": "Patent keyword should trigger PatentAgent"
        },
        {
            "query": "FDA approval pathway for biosimilars",
            "expected_agents": ["EXIMAgent"],
            "description": "Regulatory keyword should trigger EXIMAgent"
        },
        {
            "query": "Mechanism and PK/PD of semaglutide",
            "expected_agents": ["PKPDAgent"],
            "description": "Mechanism keyword should trigger PKPDAgent"
        },
        {
            "query": "Recent publications on immunotherapy",
            "expected_agents": ["WebIntelAgent"],
            "description": "Recent keyword should trigger WebIntelAgent"
        },
        {
            "query": "Comprehensive diabetes drug landscape with market, trials, and patents",
            "expected_agents": ["MarketAgent", "ClinicalTrialsAgent", "PatentAgent"],
            "description": "Multiple keywords should trigger multiple agents"
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        query = test["query"]
        expected_agents = set(test["expected_agents"])
        description = test["description"]
        
        # Detect mode
        classification = detect_research_mode(query)
        actual_agents = set(classification.required_agents)
        
        # Check if expected agents are included
        has_expected = expected_agents.issubset(actual_agents)
        
        if has_expected:
            passed += 1
            status = "✅ PASS"
        else:
            failed += 1
            status = "❌ FAIL"
        
        print(f"{i}. {status}")
        print(f"   Query: \"{query}\"")
        print(f"   Expected Agents: {sorted(expected_agents)}")
        print(f"   Actual Agents: {sorted(actual_agents)}")
        print(f"   Description: {description}")
        print()
    
    # Summary
    print("="*80)
    print(f"📊 AGENT SELECTION SUMMARY")
    print("="*80)
    print(f"Total Tests: {len(test_cases)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/len(test_cases)*100):.1f}%")
    print("="*80)
    
    if failed == 0:
        print("\n🎉 ALL AGENT SELECTION TESTS PASSED! 🎉\n")
    else:
        print(f"\n⚠️  {failed} tests failed. Review agent selection logic.\n")
    
    return failed == 0


if __name__ == "__main__":
    # Run all tests
    mode_test_passed = test_auto_mode_detection()
    agent_test_passed = test_agent_auto_selection()
    
    # Overall result
    print("\n" + "="*80)
    print("🏁 FINAL RESULT")
    print("="*80)
    
    if mode_test_passed and agent_test_passed:
        print("\n✅ ALL AUTO-MODE INTELLIGENCE TESTS PASSED!")
        print("🎯 System can automatically detect mode without user specification")
        print("🤖 Agents are correctly auto-selected based on query keywords")
        print("\nAvalon is ready for production! 🚀\n")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Review mode detection and agent selection logic.\n")
        sys.exit(1)
