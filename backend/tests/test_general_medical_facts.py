"""
Test suite for General Medical Facts exception.
Verifies that basic medical questions are answered directly without agents.
"""
import pytest
from app.agents.master_agent import MasterAgent


@pytest.fixture
def master_agent():
    """Create a MasterAgent instance for testing."""
    return MasterAgent()


def test_is_general_medical_fact_side_effects(master_agent):
    """Test detection of side effects questions."""
    queries = [
        "What are side effects of aspirin?",
        "Side effects of metformin",
        "adverse effects of warfarin",
        "What are the side effects of ibuprofen?"
    ]
    for query in queries:
        assert master_agent.is_general_medical_fact(query), f"Should detect: {query}"


def test_is_general_medical_fact_mechanism(master_agent):
    """Test detection of mechanism questions."""
    queries = [
        "Mechanism of action of insulin",
        "How does paracetamol work?",
        "What does aspirin do?",
        "mechanism of action of metformin"
    ]
    for query in queries:
        assert master_agent.is_general_medical_fact(query), f"Should detect: {query}"


def test_is_general_medical_fact_indications(master_agent):
    """Test detection of indication/use questions."""
    queries = [
        "What is metformin used for?",
        "What are aspirin indications?",
        "Common uses of ibuprofen",
        "What is insulin indicated for?"
    ]
    for query in queries:
        assert master_agent.is_general_medical_fact(query), f"Should detect: {query}"


def test_is_general_medical_fact_drug_interactions(master_agent):
    """Test detection of drug interaction questions."""
    queries = [
        "Drug interactions with warfarin",
        "What drugs interact with aspirin?",
        "drug interactions of metformin"
    ]
    for query in queries:
        assert master_agent.is_general_medical_fact(query), f"Should detect: {query}"


def test_is_general_medical_fact_pk_pd(master_agent):
    """Test detection of basic PK/PD questions."""
    queries = [
        "half-life of aspirin",
        "pharmacokinetics of metformin",
        "What is the half life of warfarin?",
        "pharmacodynamics of insulin"
    ]
    for query in queries:
        assert master_agent.is_general_medical_fact(query), f"Should detect: {query}"


def test_is_general_medical_fact_dosage(master_agent):
    """Test detection of dosage questions."""
    queries = [
        "dosage of aspirin",
        "What is the typical dose of metformin?",
        "How much ibuprofen should I take?"
    ]
    for query in queries:
        assert master_agent.is_general_medical_fact(query), f"Should detect: {query}"


def test_is_general_medical_fact_contraindications(master_agent):
    """Test detection of contraindication questions."""
    queries = [
        "contraindications for aspirin",
        "What are contraindications of warfarin?",
        "contraindications for metformin"
    ]
    for query in queries:
        assert master_agent.is_general_medical_fact(query), f"Should detect: {query}"


def test_is_NOT_general_medical_fact_market(master_agent):
    """Test that market questions are NOT detected as general medical facts."""
    queries = [
        "Market size of aspirin",
        "What is the CAGR for diabetes drugs?",
        "Commercial forecast for metformin",
        "Revenue of insulin market"
    ]
    for query in queries:
        assert not master_agent.is_general_medical_fact(query), f"Should NOT detect: {query}"


def test_is_NOT_general_medical_fact_trials(master_agent):
    """Test that clinical trial questions are NOT detected as general medical facts."""
    queries = [
        "Clinical trials for aspirin in cancer",
        "Phase 3 trials of metformin",
        "What are the ongoing trials for insulin?",
        "Trial results for diabetes drugs"
    ]
    for query in queries:
        assert not master_agent.is_general_medical_fact(query), f"Should NOT detect: {query}"


def test_is_NOT_general_medical_fact_patents(master_agent):
    """Test that patent questions are NOT detected as general medical facts."""
    queries = [
        "Patent landscape for aspirin",
        "When does metformin patent expire?",
        "Insulin patent status",
        "IP protection for diabetes drugs"
    ]
    for query in queries:
        assert not master_agent.is_general_medical_fact(query), f"Should NOT detect: {query}"


def test_is_NOT_general_medical_fact_complex(master_agent):
    """Test that complex analytical questions are NOT detected as general medical facts."""
    queries = [
        "Comprehensive analysis of aspirin market and clinical evidence",
        "What are the repurposing opportunities for metformin in rare diseases?",
        "Competitive landscape analysis for GLP-1 agonists",
        "Market dynamics and unmet needs in diabetes treatment"
    ]
    for query in queries:
        assert not master_agent.is_general_medical_fact(query), f"Should NOT detect: {query}"


def test_common_drug_short_question(master_agent):
    """Test that short questions about common drugs are detected."""
    queries = [
        "aspirin uses",
        "metformin effects",
        "insulin indication",
        "warfarin interactions"
    ]
    for query in queries:
        assert master_agent.is_general_medical_fact(query), f"Should detect: {query}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
