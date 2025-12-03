from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict

from app.agents.workers.expert_network_agent import ExpertNetworkAgent
from app.services.graph_builder import GraphBuilder

router = APIRouter()


class GraphBuildRequest(BaseModel):
    query: str = Field(..., min_length=3)
    signals: Dict[str, Any] = Field(default_factory=dict)


@router.post("/build")
async def build_graph(request: GraphBuildRequest):
    agent = ExpertNetworkAgent(worker_id="graph_api")
    try:
        result = await agent.process("build_graph", request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="graph_build_failure") from exc
    return result


@router.get("/{graph_id}")
async def get_graph(graph_id: str):
    builder = GraphBuilder()
    try:
        graph = builder.load_graph(graph_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return graph


