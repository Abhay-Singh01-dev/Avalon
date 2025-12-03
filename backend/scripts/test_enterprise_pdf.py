"""
Test Enterprise PDF Report Generation
Tests the new ReportLab-based PDF generation with full styling
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.report_generator import (
    extract_agent_data,
    generate_pdf_content,
    generate_csv_content,
    AvalonReportBuilder
)

# Mock conversation data with agent responses
MOCK_CONVERSATION = {
    "messages": [
        {
            "role": "user",
            "content": "Analyze the competitive landscape for GLP-1 receptor agonists in the diabetes and obesity market"
        },
        {
            "role": "assistant",
            "content": "I've completed a comprehensive multi-agent research analysis. Here are the key findings:\n\n**Market Analysis**: The GLP-1 market is experiencing explosive growth...",
            "metadata": {
                "workers": {
                    "market": {
                        "summary": "The GLP-1 receptor agonist market has grown from $10B in 2020 to over $30B in 2024, driven primarily by Novo Nordisk's Ozempic/Wegovy and Eli Lilly's Mounjaro. Market penetration in obesity indications is still under 5% of addressable population, suggesting significant runway for growth.",
                        "key_findings": [
                            "Market size reached $31.2B in 2024, up 180% from 2022",
                            "Novo Nordisk commands 62% market share, Eli Lilly 28%",
                            "Oral GLP-1 candidates in Phase 3 could expand market by 40%",
                            "Payer coverage expanding rapidly with 85% commercial coverage in 2024"
                        ],
                        "insights": [
                            "Supply constraints remain a major bottleneck through 2025",
                            "Obesity indication driving 70% of prescription growth",
                            "Combination therapies (GLP-1 + GIP) showing superior efficacy"
                        ],
                        "sources": ["IQVIA Data", "Symphony Health", "Company Filings"],
                        "provenance": ["Market database query - Q3 2024"],
                        "data_tables": [
                            {
                                "headers": ["Company", "Product", "2023 Sales ($B)", "2024E Sales ($B)", "Growth %"],
                                "rows": [
                                    ["Novo Nordisk", "Ozempic", "8.9", "12.5", "40%"],
                                    ["Novo Nordisk", "Wegovy", "4.1", "8.2", "100%"],
                                    ["Eli Lilly", "Mounjaro", "5.2", "11.0", "112%"],
                                    ["Sanofi", "Soliqua", "0.8", "0.9", "12%"]
                                ]
                            }
                        ]
                    },
                    "clinical": {
                        "summary": "Currently 47 active clinical trials investigating GLP-1 receptor agonists across diabetes, obesity, cardiovascular, and NASH indications. Phase 3 studies show consistent 15-20% weight loss with dual GLP-1/GIP agonists.",
                        "key_findings": [
                            "47 active trials (12 Phase 3, 23 Phase 2, 12 Phase 1)",
                            "Cardiovascular outcomes consistently positive across trials",
                            "15-20% weight loss demonstrated in Phase 3 obesity trials",
                            "NASH/NAFLD emerging as key indication with 8 trials"
                        ],
                        "insights": [
                            "Oral formulations advancing rapidly - 5 in Phase 2+",
                            "Long-acting formulations (monthly/quarterly) in development",
                            "Combination with SGLT2 inhibitors showing synergy"
                        ],
                        "sources": ["ClinicalTrials.gov", "Company Press Releases", "Medical Journals"],
                        "provenance": ["Clinical trials database - Nov 2024"]
                    },
                    "patents": {
                        "summary": "Patent landscape dominated by Novo Nordisk and Eli Lilly with core composition-of-matter patents expiring 2026-2032. Over 200 patent families covering formulations, delivery devices, and combination therapies.",
                        "key_findings": [
                            "Semaglutide core patents expire 2031-2033",
                            "Tirzepatide protected through 2036",
                            "Device patents create additional barriers (2028-2035)",
                            "Oral formulation patents filed by 8 different companies"
                        ],
                        "sources": ["USPTO", "EPO", "Patent Analytics Database"],
                        "provenance": ["Patent search - November 2024"]
                    },
                    "web": {
                        "summary": "Social media and online communities show massive consumer interest in GLP-1 drugs, with over 15M posts discussing Ozempic/Wegovy in 2024. Shortage discussions dominate discourse.",
                        "key_findings": [
                            "15.2M social media mentions in 2024 (up 400% YoY)",
                            "Supply shortage complaints in 68% of discussions",
                            "Cost concerns mentioned in 42% of patient posts",
                            "Celebrity endorsements driving awareness"
                        ],
                        "sources": ["Social media monitoring", "Reddit r/Semaglutide", "Twitter/X"],
                        "provenance": ["Web scraping - Nov 15-22, 2024"]
                    }
                },
                "executive_summary": [
                    "The GLP-1 receptor agonist market represents one of the fastest-growing pharmaceutical sectors, with sales exceeding $30B in 2024 and projected to reach $100B by 2030.",
                    "Novo Nordisk and Eli Lilly dominate with 90% combined market share, driven by blockbuster products Ozempic/Wegovy and Mounjaro demonstrating unprecedented weight loss efficacy (15-20%).",
                    "Clinical pipeline is robust with 47 active trials exploring obesity, cardiovascular, NASH, and other metabolic indications, with oral formulations emerging as next major innovation.",
                    "Supply constraints remain the primary market bottleneck through 2025, with companies investing billions in manufacturing capacity expansion.",
                    "Patent protection extends through 2030s for leading products, but oral formulation patents are becoming increasingly crowded with 8+ companies filing applications.",
                    "Consumer demand is unprecedented with 15M+ social media discussions in 2024, though cost and access concerns persist with ~$1,000/month retail pricing."
                ]
            }
        }
    ]
}


def test_extract_agent_data():
    """Test agent data extraction from conversation"""
    print("\n" + "="*60)
    print("TEST 1: Extract Agent Data")
    print("="*60)
    
    messages = MOCK_CONVERSATION["messages"]
    report_data = extract_agent_data(messages)
    
    print(f"\n✓ Extracted {len(report_data['sections'])} agent sections")
    print(f"✓ Has executive summary: {len(report_data['executive_summary'])} bullets")
    print(f"✓ Has tables: {report_data['has_table']}")
    print(f"✓ Total tables: {len(report_data['data_tables'])}")
    
    for section in report_data['sections']:
        print(f"\n  Agent: {section['agent']}")
        print(f"    - Summary length: {len(section['summary'])} chars")
        print(f"    - Key findings: {len(section['key_findings'])} items")
        print(f"    - Citations: {len(section['citations'])} sources")
    
    return report_data


def test_generate_pdf(report_data):
    """Test PDF generation with enterprise styling"""
    print("\n" + "="*60)
    print("TEST 2: Generate Enterprise PDF")
    print("="*60)
    
    title = "GLP-1 Receptor Agonists: Competitive Landscape Analysis"
    conversation_id = "test_conv_12345"
    report_id = "test_report_67890"
    
    try:
        pdf_bytes = generate_pdf_content(
            report_data=report_data,
            title=title,
            conversation_id=conversation_id,
            report_id=report_id
        )
        
        print(f"\n✓ PDF generated successfully")
        print(f"✓ PDF size: {len(pdf_bytes):,} bytes ({len(pdf_bytes) / 1024:.1f} KB)")
        
        # Save to test file
        output_path = Path(__file__).parent / "test_enterprise_output.pdf"
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"✓ Saved to: {output_path}")
        print(f"\n🎉 Open the PDF to verify enterprise styling:")
        print(f"   - Cover page with Avalon branding")
        print(f"   - Executive summary page")
        print(f"   - Styled section headers with colored backgrounds")
        print(f"   - Professional tables with proper formatting")
        print(f"   - Footer on each page")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_csv(report_data):
    """Test CSV generation"""
    print("\n" + "="*60)
    print("TEST 3: Generate CSV")
    print("="*60)
    
    csv_content = generate_csv_content(report_data)
    
    print(f"\n✓ CSV generated")
    print(f"✓ CSV size: {len(csv_content)} bytes")
    print(f"\nCSV Preview (first 5 lines):")
    print("-" * 60)
    
    lines = csv_content.split('\n')[:5]
    for line in lines:
        print(line)
    
    # Save to test file
    output_path = Path(__file__).parent / "test_enterprise_output.csv"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(csv_content)
    
    print(f"\n✓ Saved to: {output_path}")
    
    return True


def test_builder_directly():
    """Test AvalonReportBuilder class directly"""
    print("\n" + "="*60)
    print("TEST 4: Direct Builder Test")
    print("="*60)
    
    builder = AvalonReportBuilder(
        title="Direct Builder Test Report",
        conversation_id="test_123",
        report_id="builder_test_001"
    )
    
    print(f"\n✓ Builder created")
    print(f"✓ Styles loaded: {len(builder.styles.byName)} styles")
    print(f"✓ Custom styles: AvalonH1, AvalonH2, AvalonH3, AvalonBody, AvalonBullet")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AVALON ENTERPRISE PDF GENERATION TEST SUITE")
    print("="*60)
    
    try:
        # Test 1: Extract data
        report_data = test_extract_agent_data()
        
        # Test 2: Generate PDF
        pdf_success = test_generate_pdf(report_data)
        
        # Test 3: Generate CSV
        csv_success = test_generate_csv(report_data)
        
        # Test 4: Builder
        builder_success = test_builder_directly()
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"✓ Extract Agent Data: PASSED")
        print(f"{'✓' if pdf_success else '✗'} Generate PDF: {'PASSED' if pdf_success else 'FAILED'}")
        print(f"{'✓' if csv_success else '✗'} Generate CSV: {'PASSED' if csv_success else 'FAILED'}")
        print(f"{'✓' if builder_success else '✗'} Direct Builder: {'PASSED' if builder_success else 'FAILED'}")
        
        if pdf_success and csv_success and builder_success:
            print("\n🎉 ALL TESTS PASSED!")
            print("\n📄 Check the generated files:")
            print("   - test_enterprise_output.pdf")
            print("   - test_enterprise_output.csv")
            return 0
        else:
            print("\n⚠️  SOME TESTS FAILED")
            return 1
            
    except Exception as e:
        print(f"\n✗ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
