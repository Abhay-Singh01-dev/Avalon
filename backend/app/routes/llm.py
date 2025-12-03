"""
LLM test endpoint for verifying LM Studio connection.
"""
from fastapi import APIRouter, HTTPException, status
from app.config import settings
import app.llm.lmstudio_client as lmstudio_mod
import logging

router = APIRouter(tags=["LLM"])
logger = logging.getLogger(__name__)


@router.get("/test")
async def test_llm_endpoint():
    """
    Test endpoint to verify LM Studio connection and model availability.
    Returns the response from the model to a test message.
    
    GET /api/llm/test
    """
    try:
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Your test message. Reply with: OK"}
        ]
        
        response = await lmstudio_mod.lmstudio_client.ask_llm(
            messages=test_messages,
            model=settings.LMSTUDIO_MODEL_NAME
        )
        
        return {
            "status": "success",
            "message": "LM Studio connection successful",
            "model": settings.LMSTUDIO_MODEL_NAME,
            "response": response
        }
    except Exception as e:
        logger.error(f"LLM test endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LM Studio connection failed: {str(e)}"
        )

