"""
Test Script for Report Intent Detection System
Tests all 6 verification scenarios specified in the requirements
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.utils.report_intent import should_generate_report, count_pharma_domains


def test_report_intent():
    """
    Run all 6 test cases from requirements
    """
    
    print("=" * 80)
    print("REPORT INTENT DETECTION - TEST SUITE")
    print("=" * 80)
    print()
    
    test_cases = [
        {
            "name": "Test 1: Simple medical fact (NO REPORT)",
            "prompt": "half life of digoxin",
            "mode": "chat",
            "uploaded_files_count": 0,
            "expected": False
        },
        {
            "name": "Test 2: Multi-domain pharma query (REPORT)",
            "prompt": "give market + trials + patents for semaglutide",
            "mode": "research",
            "uploaded_files_count": 0,
            "expected": True
        },
        {
            "name": "Test 3: Explicit report request (REPORT)",
            "prompt": "give a research report on semaglutide",
            "mode": "chat",
            "uploaded_files_count": 0,
            "expected": True
        },
        {
            "name": "Test 4: Simple MOA question (NO REPORT)",
            "prompt": "explain MOA of aspirin",
            "mode": "chat",
            "uploaded_files_count": 0,
            "expected": False
        },
        {
            "name": "Test 5: Multiple files uploaded (REPORT)",
            "prompt": "summarize",
            "mode": "chat",
            "uploaded_files_count": 2,
            "expected": True
        },
        {
            "name": "Test 6: Document mode (REPORT)",
            "prompt": "analyze the clinical trial data",
            "mode": "document",
            "uploaded_files_count": 0,
            "expected": True
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        result = should_generate_report(
            prompt=test["prompt"],
            mode=test["mode"],
            uploaded_files_count=test["uploaded_files_count"]
        )
        
        status = "✅ PASS" if result == test["expected"] else "❌ FAIL"
        if result == test["expected"]:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} | {test['name']}")
        print(f"  Prompt: \"{test['prompt']}\"")
        print(f"  Mode: {test['mode']} | Files: {test['uploaded_files_count']}")
        print(f"  Expected: {test['expected']} | Got: {result}")
        
        # Show domain count for multi-domain tests
        if "market" in test['prompt'] or "trial" in test['prompt']:
            domain_count = count_pharma_domains(test['prompt'])
            print(f"  Pharma domains detected: {domain_count}")
        
        print()
    
    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)
    print()
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Report intent detection system working correctly.")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed. Please review the logic.")
        return False


def test_edge_cases():
    """
    Test edge cases and boundary conditions
    """
    
    print()
    print("=" * 80)
    print("EDGE CASE TESTS")
    print("=" * 80)
    print()
    
    edge_cases = [
        {
            "name": "Empty prompt",
            "prompt": "",
            "mode": "chat",
            "uploaded_files_count": 0,
            "expected": False
        },
        {
            "name": "Very long research query",
            "prompt": "provide comprehensive analysis of semaglutide covering market size, clinical trials, patent landscape, regulatory status, competitive analysis, and safety profile",
            "mode": "research",
            "uploaded_files_count": 0,
            "expected": True  # Should trigger on multi-domain
        },
        {
            "name": "PDF keyword alone",
            "prompt": "PDF",
            "mode": "chat",
            "uploaded_files_count": 0,
            "expected": True  # Explicit keyword
        },
        {
            "name": "Exact threshold - 3 domains",
            "prompt": "market trials patents",
            "mode": "chat",
            "uploaded_files_count": 0,
            "expected": True  # Exactly 3 domains
        },
        {
            "name": "Just below threshold - 2 domains",
            "prompt": "market trials",
            "mode": "chat",
            "uploaded_files_count": 0,
            "expected": False  # Only 2 domains
        },
        {
            "name": "Single file upload",
            "prompt": "analyze this document",
            "mode": "chat",
            "uploaded_files_count": 1,
            "expected": False  # Need 2+ files
        }
    ]
    
    for test in edge_cases:
        result = should_generate_report(
            prompt=test["prompt"],
            mode=test["mode"],
            uploaded_files_count=test["uploaded_files_count"]
        )
        
        status = "✅" if result == test["expected"] else "❌"
        print(f"{status} {test['name']}: {result} (expected {test['expected']})")
    
    print()


if __name__ == "__main__":
    # Run main test suite
    main_passed = test_report_intent()
    
    # Run edge case tests
    test_edge_cases()
    
    # Exit with appropriate code
    sys.exit(0 if main_passed else 1)
