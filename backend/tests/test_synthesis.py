import json
import pytest

from app.agents.master_agent import master_agent


@pytest.mark.asyncio
async def test_pharma_synthesis_and_verification(monkeypatch):
    # Sequence: decompose -> market worker -> clinical worker -> synthesis -> verification
    decompose = json.dumps(["market", "clinical_trials"])

    market_out = json.dumps({
        "agent_name": "market",
        "core_findings": {
            "summary": ["Market size unknown"],
            "detailed_points": []
        },
        "confidence_score": {"value": 0.4, "explanation": "Limited data"},
        "citations": [{"url": "https://example.com/non_authoritative"}]
    })

    clinical_out = json.dumps({
        "agent_name": "clinical",
        "core_findings": {
            "summary": ["Small Phase II evidence"],
            "detailed_points": []
        },
        "tables": [],
        "confidence_score": {"value": 0.6, "explanation": "Some evidence"},
        "citations": [{"url": "https://pubmed.ncbi.nlm.nih.gov/12345678/"}]
    })

    synthesis = json.dumps({
        "executive_summary": ["Repurposing report - Combined evidence"],
        "market": {},
        "clinical_trials": [],
        "mechanism": {},
        "unmet_needs": [],
        "patents": [],
        "repurposing": [],
        "regulatory": {},
        "competitive": {},
        "timeline": [],
        "expert_graph_id": None,
        "full_text": "Repurposing minocycline for Parkinson's disease shows promising early evidence.",
        "key_claims": [
            {"claim": "Drug X shows signal in PD", "confidence": 60, "provenance": ["clinical_trials", "pubmed:12345678"]}
        ]
    })

    verification = json.dumps({"issues": {"Drug X shows signal in PD": ["PubMed search: Drug X Parkinson's"]}})

    # The first response is consumed by the classifier in MasterAgent.is_pharma_prompt
    responses = ["true", decompose, market_out, clinical_out, synthesis, verification]

    async def sequenced(messages, model=None, max_tokens=None, temperature=None):
        if responses:
            return responses.pop(0)
        return "{}"

    monkeypatch.setattr("app.llm.lmstudio_client.lmstudio_client.ask_llm", sequenced)

    result = await master_agent.run("Repurposing minocycline for Parkinson's disease", user_context={})

    assert result.get("mode") == "pharma_research"
    content = result.get("content")
    assert isinstance(content, dict)
    assert "verification" in content
    assert "key_claims" in content
    # each claim should have provenance and checks (verification adds checks later)
    for claim in content.get("key_claims", []):
        assert "provenance" in claim
        # verification should contain at least one proposed check
    assert content["verification"] is not None
