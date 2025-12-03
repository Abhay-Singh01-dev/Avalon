from typing import Dict, Any
import time
import json
from app.config import settings
from app.llm.lmstudio_client import lmstudio_client
from app.core.cache import cache, CacheManager
from app.core.retry import retry_llm_call
from app.core.logger import get_logger

logger = get_logger(__name__)


class ReportGeneratorAgent:
    agent_type = "report_generator"

    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.supported_tasks = ["generate_report"]

    async def process(self, task_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if task_type != "generate_report":
            raise ValueError(f"Unsupported task type: {task_type}")
        return await self.generate_report(parameters)

    async def generate_report(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        payload = {"agent": self.agent_type, "params": parameters}
        cache_key = CacheManager.make_key(payload)

        try:
            cached = cache.get(cache_key, default=None)
            if cached is not None:
                logger.info(f"ReportGeneratorAgent cache hit: {cache_key[:8]}...")
                return cached
        except Exception:
            logger.exception("Cache lookup failed for ReportGeneratorAgent")

        system_msg = (
            "You are a scientific report generator. Combine provided worker outputs into a coherent,"
            " well-structured research report. Include executive summary, methods, findings, limitations,"
            " and recommended next steps."
        )

        # 'inputs' is expected to be a dict of section->worker output
        inputs = parameters.get("inputs", {})
        user_msg = json.dumps({"inputs": inputs, "question": parameters.get("question")})

        decorated = retry_llm_call()(lmstudio_client.ask_llm)

        try:
            raw = await decorated([
                {"role": "user", "content": system_msg + "\n\n" + user_msg}
            ], model=settings.LMSTUDIO_MODEL_NAME)
        except Exception as e:
            logger.error(f"ReportGeneratorAgent LLM failure: {e}")
            return {"error": "llm_failure", "message": str(e)}

        try:
            parsed = json.loads(raw)
        except Exception:
            # If LLM returns plain text, wrap as summary
            result = {
                "section": "report",
                "summary": raw[:300],
                "details": {"text": raw},
                "confidence": 70,
                "raw": raw,
                "cache_key": cache_key
            }
            try:
                cache.set(cache_key, result)
            except Exception:
                logger.exception("Failed to cache ReportGeneratorAgent raw result")
            return result

        summary = parsed.get("summary") or "Report generated"
        details = parsed.get("details", parsed)
        confidence = int(parsed.get("confidence", 75)) if isinstance(parsed.get("confidence", 75), (int, float)) else 75
        confidence = max(0, min(100, confidence))

        result = {
            "section": "report",
            "summary": summary,
            "details": details,
            "confidence": confidence,
            "raw": raw,
            "cache_key": cache_key
        }

        try:
            cache.set(cache_key, result)
        except Exception:
            logger.exception("Failed to cache ReportGeneratorAgent result")

        logger.info(f"ReportGeneratorAgent completed in {time.time() - start:.2f}s")
        return result
