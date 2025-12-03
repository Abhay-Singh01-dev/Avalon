from typing import Any, Dict

from app.core.logger import get_logger
from app.services.graph_builder import GraphBuilder


class ExpertNetworkAgent:
    """Agent responsible for orchestrating expert network graph creation."""

    agent_type = "expert_network"

    def __init__(self, worker_id: str, graph_builder: GraphBuilder | None = None):
        self.worker_id = worker_id
        self.graph_builder = graph_builder or GraphBuilder()
        self.supported_tasks = ["build_graph"]
        self._logger = get_logger(__name__)

    async def process(self, task_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if task_type not in self.supported_tasks:
            raise ValueError(f"Unsupported task type: {task_type}")
        return await self.build_graph(parameters)

    async def build_graph(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        query = (parameters or {}).get("query")
        signals = (parameters or {}).get("signals") or {}
        if not query:
            raise ValueError("query is required to build expert network graph")

        self._logger.info("Building expert network graph for query='%s'", query)
        graph_result = await self.graph_builder.build_graph(query=query, signals=signals)

        return {
            "section": self.agent_type,
            "graph_id": graph_result["graph_id"],
            "graph": graph_result["graph"],
            "preview": graph_result["preview"],
            "provenance": list(signals.keys()),
        }


