"""
Test Strict Table Formatting for Small LLMs

Validates that the table formatter can handle messy LLM output
and produce clean, small-LLM-friendly Markdown tables.

Run: python tests/test_table_formatting.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.llm.table_formatter import (
    format_table,
    validate_and_fix_table,
    clean_llm_table_output,
    _compress_cell_content
)


def test_compress_cell_content():
    """Test cell content compression"""
    print("\n" + "="*80)
    print("TEST 1: Cell Content Compression")
    print("="*80 + "\n")
    
    test_cases = [
        {
            "input": "This is a very long sentence that exceeds the maximum word count and should be truncated",
            "expected_max_words": 10,
            "description": "Long sentence truncation"
        },
        {
            "input": "Inhibits\nserotonin\nreuptake\nin\nneurons",
            "expected_output": "Inhibits serotonin reuptake in neurons",
            "description": "Remove line breaks"
        },
        {
            "input": "Normal    excessive     whitespace",
            "expected_output": "Normal excessive whitespace",
            "description": "Clean whitespace"
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        input_text = test["input"]
        description = test["description"]
        
        result = _compress_cell_content(input_text, max_words=10)
        
        # Check word count
        word_count = len(result.split())
        is_valid = word_count <= 10
        
        # Check no line breaks
        has_line_breaks = '\n' in result or '\r' in result
        
        if is_valid and not has_line_breaks:
            passed += 1
            status = "✅ PASS"
        else:
            failed += 1
            status = "❌ FAIL"
        
        print(f"{i}. {status} - {description}")
        print(f"   Input: \"{input_text[:50]}...\"")
        print(f"   Output: \"{result}\"")
        print(f"   Word Count: {word_count} (max 10)")
        print(f"   Has Line Breaks: {has_line_breaks}")
        print()
    
    print(f"Compression Tests: {passed} passed, {failed} failed\n")
    return failed == 0


def test_format_table():
    """Test strict table formatting"""
    print("="*80)
    print("TEST 2: Strict Table Formatting")
    print("="*80 + "\n")
    
    # Sample data
    rows = [
        {
            "Drug": "Metformin",
            "Class": "Biguanide",
            "MOA": "Reduces hepatic glucose production and increases insulin sensitivity in peripheral tissues"
        },
        {
            "Drug": "Glipizide",
            "Class": "Sulfonylurea",
            "MOA": "Stimulates insulin secretion from pancreatic beta cells by closing ATP-sensitive potassium channels"
        },
    ]
    
    table = format_table(rows, max_rows=6, max_cols=3)
    
    print("Generated Table:")
    print(table)
    print()
    
    # Validate
    lines = table.split('\n')
    
    checks = {
        "Has header row": len(lines) >= 3,
        "Has separator row": len(lines) >= 2 and '----------' in lines[1],
        "All rows have pipes": all('|' in line for line in lines),
        "No line breaks in cells": '\n' not in table.replace('\n', '||'),
    }
    
    # Check cell word counts
    max_words_per_cell = 0
    for line in lines[2:]:  # Skip header and separator
        cells = [c.strip() for c in line.split('|')[1:-1]]
        for cell in cells:
            words = len(cell.split())
            max_words_per_cell = max(max_words_per_cell, words)
    
    checks["Max words per cell <= 10"] = max_words_per_cell <= 10
    
    all_passed = all(checks.values())
    
    print("Validation Checks:")
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}")
    
    print(f"\nMax words in any cell: {max_words_per_cell}")
    print(f"\nTable Format Test: {'✅ PASS' if all_passed else '❌ FAIL'}\n")
    
    return all_passed


def test_fix_malformed_table():
    """Test fixing malformed LLM output"""
    print("="*80)
    print("TEST 3: Fix Malformed Table")
    print("="*80 + "\n")
    
    # Simulate messy LLM output
    messy_table = """| Drug | Mechanism of Action | Side Effects |
|------|---------------------|--------------|
| Metformin | This medication works by decreasing
the amount of glucose that is produced
by the liver and also increases
insulin sensitivity in muscle tissue | Common side effects include gastrointestinal
upset, nausea, diarrhea, and in rare cases
lactic acidosis which can be fatal |
| Glipizide | Works by stimulating insulin secretion | Hypoglycemia, weight gain |"""
    
    print("Messy LLM Output:")
    print(messy_table)
    print("\n" + "-"*80 + "\n")
    
    # Fix it
    fixed_table = validate_and_fix_table(messy_table, max_cols=3)
    
    print("Fixed Table:")
    print(fixed_table)
    print()
    
    # Validate
    lines = fixed_table.split('\n')
    
    # Check all rows have same column count
    col_counts = []
    for line in lines:
        if '|' in line:
            cols = len([c for c in line.split('|') if c.strip()])
            col_counts.append(cols)
    
    equal_cols = len(set(col_counts)) == 1
    
    # Check no multiline cells
    no_multiline = all('\n' not in cell for line in lines for cell in line.split('|'))
    
    # Check word counts
    max_words = 0
    for line in lines[2:]:  # Skip header and separator
        cells = [c.strip() for c in line.split('|')[1:-1]]
        for cell in cells:
            words = len(cell.split())
            max_words = max(max_words, words)
    
    within_limit = max_words <= 10
    
    checks = {
        "Equal column counts": equal_cols,
        "No multiline cells": no_multiline,
        "Max words per cell <= 10": within_limit,
    }
    
    all_passed = all(checks.values())
    
    print("Validation Checks:")
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}")
    
    print(f"\nMax words in any cell: {max_words}")
    print(f"\nFix Malformed Table Test: {'✅ PASS' if all_passed else '❌ FAIL'}\n")
    
    return all_passed


def test_clean_llm_output():
    """Test cleaning full LLM response with embedded table"""
    print("="*80)
    print("TEST 4: Clean Full LLM Response")
    print("="*80 + "\n")
    
    # Simulate LLM response with messy table
    llm_response = """Here is the comparison you requested:

| Drug | Class | Mechanism |
|------|-------|-----------|
| Metformin | Biguanide | This drug works by reducing
glucose production in the liver
and improving insulin sensitivity
in muscle and fat tissue | 
| Insulin | Hormone | Naturally occurring hormone
that regulates blood glucose
by facilitating cellular uptake |

I hope this helps!"""
    
    print("Original LLM Response:")
    print(llm_response)
    print("\n" + "-"*80 + "\n")
    
    # Clean it
    cleaned_response = clean_llm_table_output(llm_response)
    
    print("Cleaned Response:")
    print(cleaned_response)
    print()
    
    # Validate - table should be fixed
    has_table = '|' in cleaned_response
    lines = [l for l in cleaned_response.split('\n') if '|' in l]
    
    if lines:
        # Check cells are compressed
        max_words = 0
        for line in lines[2:]:  # Skip header and separator
            if '----------' in line:
                continue
            cells = [c.strip() for c in line.split('|')[1:-1]]
            for cell in cells:
                words = len(cell.split())
                max_words = max(max_words, words)
        
        within_limit = max_words <= 10
    else:
        within_limit = False
    
    all_passed = has_table and within_limit
    
    print(f"Has table: {'✅' if has_table else '❌'}")
    print(f"Cells compressed (<= 10 words): {'✅' if within_limit else '❌'}")
    print(f"Max words in any cell: {max_words if has_table else 'N/A'}")
    print(f"\nClean LLM Output Test: {'✅ PASS' if all_passed else '❌ FAIL'}\n")
    
    return all_passed


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 STRICT TABLE FORMATTING TEST SUITE")
    print("="*80)
    
    # Run all tests
    test1 = test_compress_cell_content()
    test2 = test_format_table()
    test3 = test_fix_malformed_table()
    test4 = test_clean_llm_output()
    
    # Summary
    print("="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    results = {
        "Cell Compression": test1,
        "Strict Table Format": test2,
        "Fix Malformed Table": test3,
        "Clean LLM Output": test4,
    }
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("="*80)
    
    if passed == total:
        print("\n🎉 ALL TABLE FORMATTING TESTS PASSED! 🎉")
        print("✅ Small-LLM-friendly tables are working correctly\n")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed\n")
        sys.exit(1)
