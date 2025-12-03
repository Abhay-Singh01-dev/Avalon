"""Simple tracing utility to record steps and checkpoints for auditability."""
from typing import List, Dict, Any
import time


class TraceManager:
    def __init__(self):
        self._trace: List[Dict[str, Any]] = []

    def append(self, step: str, data: Dict[str, Any]):
        self._trace.append({
            "ts": time.time(),
            "step": step,
            "data": data
        })

    def get_trace(self) -> List[Dict[str, Any]]:
        return self._trace


trace = TraceManager()
