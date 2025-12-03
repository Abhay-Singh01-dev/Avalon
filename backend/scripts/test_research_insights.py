"""
Test script for RESEARCH_INSIGHTS_TABLE mode

This script tests:
1. Detection of research insights keywords
2. Compilation of insights from worker results
3. Schema validation
4. Depth/status calculation logic
"""

import asyncio
from app.agents.master_agent import master_agent

async def test_research_insights_detection():
    """Test keyword detection for research insights mode"""
    print("=" * 80)
    print("TEST 1: Keyword Detection")
    print("=" * 80)
    
    test_queries = [
        "Provide comprehensive market analysis for diabetes drugs",
        "What is the competitive landscape for GLP-1 agonists?",
        "Generate research insights table for CAR-T therapy",
        "Show me insights table on obesity medications",
        "What are the side effects of metformin?",  # Should NOT trigger
    ]
    
    for query in test_queries:
        query_lower = query.lower()
        research_insights_keywords = [
            "research insights", "insights table", "comprehensive analysis",
            "market analysis", "competitive landscape", "landscape analysis",
            "research report", "full analysis", "detailed insights"
        ]
        
        enable_research_insights = any(keyword in query_lower for keyword in research_insights_keywords)
        print(f"\nQuery: {query}")
        print(f"  → Research Insights Enabled: {enable_research_insights}")
    
    print("\n" + "=" * 80)

async def test_insights_extraction():
    """Test extraction methods on mock worker data"""
    print("=" * 80)
    print("TEST 2: Key Findings Extraction")
    print("=" * 80)
    
    # Mock worker result
    mock_result = {
        "full_text": """
Global diabetes drug market reached $50B in 2023.
CAGR of 8.5% expected through 2030.
Key players: Novo Nordisk (35%), Eli Lilly (25%), Sanofi (15%).
GLP-1 agonists dominate with 45% market share.
Emerging markets show 12% annual growth.
        """,
        "metadata": {
            "sources": [
                {"url": "https://pubmed.ncbi.nlm.nih.gov/12345"},
                {"url": "https://clinicaltrials.gov/ct2/show/NCT12345"}
            ]
        }
    }
    
    # Test key findings extraction
    findings = master_agent._extract_key_findings(mock_result["full_text"])
    print(f"\nExtracted {len(findings)} key findings:")
    for i, finding in enumerate(findings, 1):
        print(f"  {i}. {finding}")
    
    # Test depth calculation
    depth = master_agent._calculate_depth(mock_result)
    print(f"\nCalculated Depth: {depth}")
    
    # Test link extraction
    links = master_agent._extract_links(mock_result)
    print(f"\nExtracted Links ({len(links)}):")
    for i, link in enumerate(links, 1):
        print(f"  Source {i}: {link}")
    
    # Test status determination
    status = master_agent._determine_status(mock_result, findings)
    print(f"\nDetermined Status: {status}")
    
    print("\n" + "=" * 80)

async def test_insights_compilation():
    """Test full insights table compilation from multiple workers"""
    print("=" * 80)
    print("TEST 3: Full Insights Table Compilation")
    print("=" * 80)
    
    # Mock worker results
    mock_worker_results = {
        "market": {
            "full_text": "Global diabetes drug market: $50B (2023). CAGR: 8.5%. Key players: Novo Nordisk (35%), Eli Lilly (25%).",
            "metadata": {"sources": [{"url": "https://example.com/market"}]}
        },
        "clinical_trials": {
            "full_text": "142 active trials for GLP-1 agonists. Phase 3: 28 trials. Top indication: Type 2 diabetes (85 trials).",
            "metadata": {"sources": [{"url": "https://clinicaltrials.gov/search"}]}
        },
        "patents": {
            "full_text": "325 active patents for diabetes treatments. Expiring 2025-2027: 87 patents. Top assignees: Novo Nordisk, Eli Lilly.",
            "metadata": {"sources": []}
        },
        "safety": {
            "full_text": "No data available for safety profile.",
            "metadata": {"sources": []}
        }
    }
    
    # Compile insights table
    insights_table = await master_agent._build_research_insights_table(
        mock_worker_results,
        "Provide market analysis for diabetes drugs",
        emit_timeline=None
    )
    
    print(f"\nCompiled Insights Table with {len(insights_table)} sections:\n")
    
    for i, insight in enumerate(insights_table, 1):
        print(f"{i}. {insight['section']}")
        print(f"   Depth: {insight['depth']}")
        print(f"   Status: {insight['status']}")
        print(f"   Key Findings ({len(insight['key_findings'])}):")
        for finding in insight['key_findings']:
            print(f"     • {finding}")
        print(f"   Links: {len(insight['links'])} sources")
        print(f"   Visualization: {insight['visualization'] or 'None'}")
        print()
    
    print("=" * 80)

async def test_schema_validation():
    """Test Pydantic schema validation"""
    print("=" * 80)
    print("TEST 4: Schema Validation")
    print("=" * 80)
    
    from app.schemas.chat_schema import ResearchInsightRow, ResearchInsightsTable
    
    # Valid insight row
    try:
        insight = ResearchInsightRow(
            section="Market Insights",
            key_findings=[
                "Global market size: $50B",
                "CAGR: 8.5%",
                "Key players: Novo Nordisk, Eli Lilly"
            ],
            depth="High",
            visualization="market_chart",
            links=["https://example.com/source1"],
            status="Complete"
        )
        print("✓ Valid ResearchInsightRow created successfully")
        print(f"  Section: {insight.section}")
        print(f"  Depth: {insight.depth}")
        print(f"  Status: {insight.status}")
    except Exception as e:
        print(f"✗ Error creating ResearchInsightRow: {e}")
    
    # Invalid depth value (should fail)
    try:
        invalid_insight = ResearchInsightRow(
            section="Test",
            key_findings=["Test finding"],
            depth="Invalid",  # This should fail
            visualization=None,
            links=[],
            status="Complete"
        )
        print("✗ Invalid depth value accepted (should have failed!)")
    except Exception as e:
        print(f"✓ Invalid depth correctly rejected: {type(e).__name__}")
    
    # Create full table
    try:
        table = ResearchInsightsTable(insights=[insight])
        print(f"✓ ResearchInsightsTable created with {len(table.insights)} insights")
    except Exception as e:
        print(f"✗ Error creating ResearchInsightsTable: {e}")
    
    print("\n" + "=" * 80)

async def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "RESEARCH INSIGHTS TABLE - TEST SUITE" + " " * 21 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    await test_research_insights_detection()
    await test_insights_extraction()
    await test_insights_compilation()
    await test_schema_validation()
    
    print("\n✅ All tests completed!\n")

if __name__ == "__main__":
    asyncio.run(main())
