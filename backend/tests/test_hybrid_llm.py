"""
Hybrid LLM Architecture - Test Suite

Tests the new dual-layer LLM routing system with:
- Mode classification (PATIENT, RESEARCH, DOCUMENT, TABLE, SAFETY, SIMPLE)
- Engine selection (local vs cloud)
- Agent selection
- PHI detection
- Table formatting
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.llm.llm_router import llm_router, LLMEngine
from app.llm.mode_classifier import detect_research_mode, get_mode_explanation, ChatMode
from app.llm.table_formatter import format_table, enforce_table_quality, add_hallucination_protection


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


async def test_mode_classification():
    """Test mode classification for various prompts"""
    print_section("MODE CLASSIFICATION TESTS")
    
    test_cases = [
        # PATIENT MODE
        ("My patient has HbA1c 8.9%, weight 108 kg, on metformin", ChatMode.PATIENT),
        ("Patient name: John Doe, BP: 140/90, adjust medication", ChatMode.PATIENT),
        
        # SAFETY MODE
        ("What's the weather today?", ChatMode.SAFETY),
        ("Tell me a joke", ChatMode.SAFETY),
        
        # DOCUMENT MODE
        ("Analyze this clinical trial PDF document", ChatMode.DOCUMENT),
        ("Summarize the uploaded file", ChatMode.DOCUMENT),
        
        # TABLE MODE
        ("Create a comparison table of GLP-1 agonists", ChatMode.TABLE),
        ("Make a table comparing metformin vs glipizide", ChatMode.TABLE),
        
        # SIMPLE MODE
        ("What is metformin?", ChatMode.SIMPLE),
        ("List the side effects of aspirin", ChatMode.SIMPLE),
        
        # RESEARCH MODE
        ("Comprehensive analysis of SGLT2 inhibitors market landscape", ChatMode.RESEARCH),
        ("Latest clinical trials for Alzheimer's disease treatments", ChatMode.RESEARCH),
    ]
    
    passed = 0
    failed = 0
    
    for prompt, expected_mode in test_cases:
        classification = detect_research_mode(prompt)
        
        if classification.mode == expected_mode:
            print(f"✅ PASS: {prompt[:60]}")
            print(f"   Mode: {classification.mode} | Reason: {classification.reason}")
            passed += 1
        else:
            print(f"❌ FAIL: {prompt[:60]}")
            print(f"   Expected: {expected_mode}, Got: {classification.mode}")
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"Mode Classification: {passed} passed, {failed} failed")
    return passed, failed


async def test_engine_selection():
    """Test LLM engine selection logic"""
    print_section("ENGINE SELECTION TESTS")
    
    test_cases = [
        # Should use local
        ("What is insulin?", "simple", LLMEngine.LOCAL),
        ("My patient has diabetes", "patient", LLMEngine.LOCAL),
        ("Create a table of statins", "table", LLMEngine.LOCAL),
        
        # Would use cloud if enabled (but currently disabled)
        ("Comprehensive 20+ citation analysis of GLP-1 market", "research", LLMEngine.LOCAL),
    ]
    
    passed = 0
    failed = 0
    
    for prompt, mode, expected_engine in test_cases:
        engine_choice = await llm_router.choose_engine(prompt, mode)
        
        if engine_choice["engine"] == expected_engine:
            print(f"✅ PASS: {prompt[:60]}")
            print(f"   Engine: {engine_choice['engine']} | Reason: {engine_choice['reason']}")
            passed += 1
        else:
            print(f"❌ FAIL: {prompt[:60]}")
            print(f"   Expected: {expected_engine}, Got: {engine_choice['engine']}")
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"Engine Selection: {passed} passed, {failed} failed")
    return passed, failed


async def test_phi_detection():
    """Test PHI detection in prompts"""
    print_section("PHI DETECTION TESTS")
    
    test_cases = [
        ("My patient has HbA1c 8.9%", True),
        ("Patient name: John Doe, MRN: 12345", True),
        ("What is metformin used for?", False),
        ("Compare diabetes drugs", False),
        ("Patient: Jane Smith, age: 45, weight: 70kg", True),
        ("General question about insulin", False),
    ]
    
    passed = 0
    failed = 0
    
    for prompt, should_contain_phi in test_cases:
        contains_phi = llm_router._contains_phi(prompt)
        
        if contains_phi == should_contain_phi:
            print(f"✅ PASS: {prompt[:60]}")
            print(f"   PHI detected: {contains_phi}")
            passed += 1
        else:
            print(f"❌ FAIL: {prompt[:60]}")
            print(f"   Expected PHI: {should_contain_phi}, Got: {contains_phi}")
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"PHI Detection: {passed} passed, {failed} failed")
    return passed, failed


def test_table_formatting():
    """Test table formatting utilities"""
    print_section("TABLE FORMATTING TESTS")
    
    # Test data
    rows = [
        {"Drug": "Metformin", "Class": "Biguanide", "MOA": "Reduces glucose"},
        {"Drug": "Glipizide", "Class": "Sulfonylurea", "MOA": "Increases insulin"},
        {"Drug": "Insulin", "Class": "Hormone", "MOA": "Replaces insulin"},
    ]
    
    table = format_table(rows, max_rows=6, max_cols=3)
    
    print("Generated Table:")
    print(table)
    
    # Validate table structure
    lines = table.split("\n")
    has_header = len(lines) >= 1 and "|" in lines[0]
    has_separator = len(lines) >= 2 and "---" in lines[1]
    has_data = len(lines) >= 3
    
    if has_header and has_separator and has_data:
        print("\n✅ PASS: Table structure valid")
        return 1, 0
    else:
        print("\n❌ FAIL: Table structure invalid")
        return 0, 1


def test_hallucination_protection():
    """Test hallucination protection system prompt"""
    print_section("HALLUCINATION PROTECTION TEST")
    
    original_prompt = "You are a pharmaceutical assistant."
    enhanced_prompt = add_hallucination_protection(original_prompt)
    
    has_rules = "STRICT QUALITY RULES" in enhanced_prompt
    has_unknown = "Unknown" in enhanced_prompt
    
    if has_rules and has_unknown:
        print("✅ PASS: Hallucination rules added")
        print(f"   Original length: {len(original_prompt)} chars")
        print(f"   Enhanced length: {len(enhanced_prompt)} chars")
        return 1, 0
    else:
        print("❌ FAIL: Hallucination rules not properly added")
        return 0, 1


async def test_cloud_disabled():
    """Test that cloud calls return appropriate errors"""
    print_section("CLOUD DISABLED TEST")
    
    messages = [{"role": "user", "content": "Test prompt"}]
    
    try:
        response = await llm_router.ask_cloud(messages)
        
        # Should return error JSON
        if "error" in response.lower() and "disabled" in response.lower():
            print("✅ PASS: Cloud returns disabled error")
            print(f"   Response: {response[:100]}")
            return 1, 0
        else:
            print("❌ FAIL: Cloud didn't return expected error")
            return 0, 1
    except Exception as e:
        print(f"❌ FAIL: Unexpected exception: {str(e)}")
        return 0, 1


async def test_local_fallback():
    """Test that local fallback works when cloud is requested but disabled"""
    print_section("LOCAL FALLBACK TEST")
    
    # Prompt that would prefer cloud but cloud is disabled
    prompt = "Comprehensive 20+ citation meta-analysis"
    
    engine_choice = await llm_router.choose_engine(prompt, "research")
    
    # Should choose local since cloud is disabled
    if engine_choice["engine"] == LLMEngine.LOCAL:
        print("✅ PASS: Falls back to local when cloud disabled")
        print(f"   Reason: {engine_choice['reason']}")
        return 1, 0
    else:
        print("❌ FAIL: Didn't fall back to local")
        return 0, 1


async def run_all_tests():
    """Run all test suites"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "HYBRID LLM ARCHITECTURE TEST SUITE" + " " * 24 + "║")
    print("╚" + "=" * 78 + "╝")
    
    total_passed = 0
    total_failed = 0
    
    # Run tests
    p, f = await test_mode_classification()
    total_passed += p
    total_failed += f
    
    p, f = await test_engine_selection()
    total_passed += p
    total_failed += f
    
    p, f = await test_phi_detection()
    total_passed += p
    total_failed += f
    
    p, f = test_table_formatting()
    total_passed += p
    total_failed += f
    
    p, f = test_hallucination_protection()
    total_passed += p
    total_failed += f
    
    p, f = await test_cloud_disabled()
    total_passed += p
    total_failed += f
    
    p, f = await test_local_fallback()
    total_passed += p
    total_failed += f
    
    # Summary
    print_section("TEST SUMMARY")
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Success Rate: {(total_passed / (total_passed + total_failed) * 100):.1f}%")
    
    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print(f"\n⚠️  {total_failed} tests failed")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
