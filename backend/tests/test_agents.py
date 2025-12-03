import asyncio
import json
import pytest
from app.core import cache as cache_mod


class InMemoryCache:
    def __init__(self):
        self._store = {}

    def get(self, key, default=None):
        return self._store.get(key, default)

    def set(self, key, value):
        self._store[key] = value

    def clear(self):
        self._store.clear()

    def flushall(self):
        self.clear()


@pytest.fixture(autouse=True)
def patch_inmemory_cache(monkeypatch):
    mem_cache = InMemoryCache()
    monkeypatch.setattr(cache_mod, "cache", mem_cache)
    monkeypatch.setattr("app.agents.workers.market_agent.cache", mem_cache)
    monkeypatch.setattr("app.agents.workers.clinical_trials_agent.cache", mem_cache)
    monkeypatch.setattr("app.agents.workers.patent_agent.cache", mem_cache)
    yield


from app.agents.workers.market_agent import MarketAgent
from app.agents.workers.clinical_trials_agent import ClinicalTrialsAgent
from app.agents.workers.patent_agent import PatentAgent
from app.agents.master_agent import master_agent


@pytest.mark.asyncio
async def test_market_agent_calls_lmstudio(monkeypatch):
    sample_response = json.dumps({
        "agent_name": "market",
        "core_findings": {
            "summary": ["Estimated market size is data not available"],
            "detailed_points": []
        },
        "tables": [],
        "key_insights": [],
        "confidence_score": {"value": 0.5, "explanation": "Limited data"}
    })

    async def fake_ask(messages, model=None, max_tokens=None, temperature=None):
        return sample_response

    monkeypatch.setattr("app.llm.lmstudio_client.lmstudio_client.ask_llm", fake_ask)

    agent = MarketAgent("test_market")
    res = await agent.analyze_section({"query": "metformin market analysis", "context": {"country": "India"}})

    assert res["agent_name"] in ["market", "IQVIA", "Market"]  # Accept various agent name formats
    assert "core_findings" in res
    assert "summary" in res["core_findings"]


@pytest.mark.asyncio
async def test_clinical_agent_parses_trials(monkeypatch):
    sample_response = json.dumps({
        "agent_name": "clinical",
        "core_findings": {
            "summary": ["Found trials for tocilizumab"],
            "detailed_points": []
        },
        "tables": [{"title": "Trials", "columns": ["id", "phase"], "rows": [["NCT123", "3"]]}],
        "key_insights": [],
        "confidence_score": {"value": 0.8, "explanation": "Good data"}
    })

    async def fake_ask(messages, model=None, max_tokens=None, temperature=None):
        return sample_response

    monkeypatch.setattr("app.llm.lmstudio_client.lmstudio_client.ask_llm", fake_ask)

    agent = ClinicalTrialsAgent("test_ct")
    res = await agent.analyze_section({"query": "tocilizumab clinical trials", "context": {}})

    assert res["agent_name"] in ["clinical", "ClinicalTrials", "Clinical"]  # Accept various agent name formats
    assert "core_findings" in res
    assert isinstance(res["tables"], list)


@pytest.mark.asyncio
async def test_patent_agent_returns_list(monkeypatch):
    sample_response = json.dumps({
        "agent_name": "patents",
        "core_findings": {
            "summary": ["Patent landscape for adalimumab"],
            "detailed_points": []
        },
        "tables": [{"title": "Patents", "columns": ["title", "assignee"], "rows": [["Example", "Company"]]}],
        "key_insights": [],
        "confidence_score": {"value": 0.7, "explanation": "Moderate data"}
    })

    async def fake_ask(messages, model=None, max_tokens=None, temperature=None):
        return sample_response

    monkeypatch.setattr("app.llm.lmstudio_client.lmstudio_client.ask_llm", fake_ask)

    agent = PatentAgent("test_patent")
    res = await agent.analyze_section({"query": "adalimumab patents", "context": {}})

    assert res["agent_name"] in ["patents", "Patent", "Patents"]  # Accept various agent name formats
    assert "core_findings" in res
    assert isinstance(res["tables"], list)


@pytest.mark.asyncio
async def test_master_agent_integration(monkeypatch):
    # Sequence: classifier yes -> decompose -> market worker -> clinical worker -> synthesis -> verification
    responses = [
        "true",  # classifier
        json.dumps(["market", "clinical"], default=str),  # decompose
        json.dumps({"section": "market", "summary": "Market output", "details": {"x": 1}, "confidence": 60}),  # market worker
        json.dumps({"section": "clinical", "summary": "Clinical output", "details": {"trials": []}, "confidence": 70}),  # clinical worker
        json.dumps({"executive_summary": ["Summary"], "market": {}, "clinical_trials": [], "mechanism": {}, "unmet_needs": [], "patents": [], "repurposing": [], "regulatory": {}, "competitive": {}, "timeline": [], "expert_graph_id": None, "full_text": "Synthesized report"}),  # synthesis
        json.dumps({"issues": {}})  # verification
    ]

    async def sequenced_ask(messages, model=None, max_tokens=None, temperature=None):
        if responses:
            return responses.pop(0)
        return "{}"

    monkeypatch.setattr("app.llm.lmstudio_client.lmstudio_client.ask_llm", sequenced_ask)

    result = await master_agent.run("Evaluate metformin in diabetes", user_context={})

    assert result.get("mode") == "pharma_research"
    assert "content" in result
    assert "workers" in result
