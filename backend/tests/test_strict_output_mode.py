"""
Test suite for Strict Output Mode implementation.
Verifies that MasterAgent outputs ONLY requested content without meta-text.
"""
import pytest
from app.agents.master_agent import MasterAgent


@pytest.fixture
def master_agent():
    """Create a MasterAgent instance for testing."""
    return MasterAgent()


def test_clean_final_output_removes_research_prefix(master_agent):
    """Test removal of 'Research analysis for:' prefix."""
    input_text = "Research analysis for: diabetes drugs. Market size is $50B."
    expected = "Market size is $50B."
    result = master_agent._clean_final_output(input_text)
    assert "Research analysis for" not in result
    assert "Market size is $50B" in result


def test_clean_final_output_removes_agent_attribution(master_agent):
    """Test removal of agent attribution text."""
    input_text = "3 agents contributed insights. The market is growing."
    expected = "The market is growing."
    result = master_agent._clean_final_output(input_text)
    assert "agents contributed" not in result
    assert "The market is growing" in result


def test_clean_final_output_removes_section_labels(master_agent):
    """Test removal of section labels like Executive Summary."""
    input_text = "Executive Summary: Market size is $50B. Key Findings: CAGR is 8%."
    result = master_agent._clean_final_output(input_text)
    assert "Executive Summary:" not in result
    assert "Key Findings:" not in result
    assert "Market size is $50B" in result
    assert "CAGR is 8%" in result


def test_clean_final_output_removes_meta_commentary(master_agent):
    """Test removal of meta-commentary phrases."""
    input_text = "In summary, the drug shows promise. As mentioned earlier, the trials are ongoing."
    result = master_agent._clean_final_output(input_text)
    assert "In summary," not in result.lower()
    assert "As mentioned earlier," not in result.lower()
    assert "the drug shows promise" in result
    assert "the trials are ongoing" in result


def test_clean_final_output_removes_filler_phrases(master_agent):
    """Test removal of generic filler phrases."""
    input_text = "Further research is needed to confirm efficacy. Studies have shown that the drug works."
    result = master_agent._clean_final_output(input_text)
    assert "Further research is needed" not in result
    assert "Studies have shown that" not in result.lower()
    # Entire filler sentence should be removed (including "to confirm efficacy")
    assert "to confirm efficacy" not in result
    # But factual content after filler should remain
    assert "the drug works" in result


def test_clean_final_output_preserves_bullet_points(master_agent):
    """Test that bullet point formatting is preserved."""
    input_text = """- Gastrointestinal bleeding
- Peptic ulcers
- Reye's syndrome"""
    result = master_agent._clean_final_output(input_text)
    # Content should be preserved
    assert "Gastrointestinal bleeding" in result
    assert "Peptic ulcers" in result
    assert "Reye's syndrome" in result


def test_clean_final_output_preserves_tables(master_agent):
    """Test that Markdown table formatting is preserved."""
    input_text = """| Drug | Indication | Market Size |
|------|------------|-------------|
| Aspirin | Pain | $2B |
| Metformin | Diabetes | $5B |"""
    result = master_agent._clean_final_output(input_text)
    assert "| Drug | Indication | Market Size |" in result
    assert "| Aspirin | Pain | $2B |" in result
    assert "| Metformin | Diabetes | $5B |" in result


def test_clean_final_output_removes_agent_names(master_agent):
    """Test removal of agent name attributions."""
    input_text = "According to the market agent, the size is $50B. MarketAgent found that CAGR is 8%."
    result = master_agent._clean_final_output(input_text)
    assert "According to the market agent" not in result.lower()
    assert "MarketAgent found" not in result
    assert "the size is $50B" in result
    assert "CAGR is 8%" in result


def test_clean_final_output_removes_verification_scaffold(master_agent):
    """Test removal of verification scaffold markers."""
    input_text = """CERTAIN FACTS: Market size is $50B.
LIKELY BUT NOT CERTAIN: CAGR is 8%.
UNCERTAIN OR CANNOT ANSWER: Future trends unclear."""
    result = master_agent._clean_final_output(input_text)
    assert "CERTAIN FACTS:" not in result
    assert "LIKELY BUT NOT CERTAIN:" not in result
    assert "UNCERTAIN OR CANNOT ANSWER:" not in result
    assert "Market size is $50B" in result
    assert "CAGR is 8%" in result


def test_clean_final_output_normalizes_whitespace(master_agent):
    """Test that excessive whitespace is normalized."""
    input_text = "Market size is $50B.\n\n\n\nCAGR is 8%."
    result = master_agent._clean_final_output(input_text)
    # Should have max 2 consecutive newlines
    assert "\n\n\n" not in result
    assert "Market size is $50B" in result
    assert "CAGR is 8%" in result


def test_clean_final_output_complex_case(master_agent):
    """Test complex case with multiple meta-text patterns."""
    input_text = """Research analysis for: aspirin side effects. 3 agents contributed insights.

Executive Summary: The following analysis covers safety data.

According to the safety agent, the main side effects are:
- Gastrointestinal bleeding
- Peptic ulcers

In summary, we found that aspirin has moderate risk."""
    
    result = master_agent._clean_final_output(input_text)
    
    # Meta-text should be removed
    assert "Research analysis for:" not in result
    assert "agents contributed" not in result
    assert "Executive Summary:" not in result
    assert "According to the safety agent" not in result.lower()
    assert "In summary," not in result.lower()
    
    # Factual content should be preserved
    assert "Gastrointestinal bleeding" in result
    assert "Peptic ulcers" in result
    assert "aspirin has moderate risk" in result


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
