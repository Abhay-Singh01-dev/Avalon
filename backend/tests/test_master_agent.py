import asyncio
import pytest

from app.agents.master_agent import MasterAgent, master_agent


class DummyLLM:
    def __init__(self, responses):
        # responses is an iterable of strings returned sequentially
        self._responses = list(responses)

    async def ask_llm(self, messages, model=None):
        if not self._responses:
            return ""
        return self._responses.pop(0)


@pytest.mark.asyncio
async def test_normal_chat_mode(monkeypatch):
    # Arrange: stub LM Studio to return a friendly chat response
    dummy = DummyLLM(["Hello — this is a normal chat reply."])
    monkeypatch.setattr("app.llm.lmstudio_client.lmstudio_client", dummy)

    # Act
    response = await master_agent.run("What is quantum physics?", user_context={})

    # Assert
    assert isinstance(response, dict)
    assert response.get("mode") == "chat"
    assert "quantum" in response.get("content", "").lower() or "hello" in response.get("content", "").lower()


@pytest.mark.asyncio
async def test_pharma_research_mode_and_workers(monkeypatch):
    # Decompose -> tells master to call market and clinical_trials
    # Then market worker returns market analysis, clinical worker returns clinical analysis
    # Final synthesis returns a combined report
    responses = [
        "true",  # classifier
        '["market", "clinical_trials"]',  # decompose
        '{"section": "market", "summary": "Market analysis output from LLM", "details": {}, "confidence": 70}',  # market worker
        '{"section": "clinical", "summary": "Clinical analysis output from LLM", "details": {}, "confidence": 80}',  # clinical worker
        '{"executive_summary": ["Summary"], "market": {}, "clinical_trials": [], "mechanism": {}, "unmet_needs": [], "patents": [], "repurposing": [], "regulatory": {}, "competitive": {}, "timeline": [], "expert_graph_id": null, "full_text": "Final synthesized Pharma report"}',  # synthesis
        "{}"  # verification
    ]

    dummy = DummyLLM(responses)
    monkeypatch.setattr("app.llm.lmstudio_client.lmstudio_client", dummy)

    # Ensure master_agent has workers registered (registry auto-registers at import)
    assert master_agent.workers

    # Act
    resp = await master_agent.run("Explain metformin mechanism of action and market potential", user_context={})

    # Assert
    assert isinstance(resp, dict)
    assert resp.get("mode") == "pharma_research"
    content = resp.get("content")
    assert isinstance(content, dict)
    workers = resp.get("workers")
    assert isinstance(workers, dict)
