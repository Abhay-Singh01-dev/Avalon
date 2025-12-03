"""
LM Studio HTTP client wrapper for LLM interactions.

This module provides an async interface to LM Studio's REST API,
which runs locally on http://localhost:1234/v1/chat/completions.
"""
import httpx
import logging
import json
from typing import List, Dict, Optional, AsyncGenerator
from app.config import settings

logger = logging.getLogger(__name__)

LMSTUDIO_API_BASE = "http://localhost:1234/v1"
LMSTUDIO_DEFAULT_MODEL = getattr(settings, "LMSTUDIO_MODEL_NAME", "mistral-7b-instruct-v0.3-q6_k")


async def ask_llm(
    messages: List[Dict[str, str]],
    model: str = LMSTUDIO_DEFAULT_MODEL,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    stream: bool = False
) -> str:
    """
    Send messages to LM Studio REST API and return the response.
    
    Args:
        messages: List of message dicts with "role" and "content" keys
        model: Model name (defaults to mistral-7b-instruct-v0.3-q6_k)
        temperature: Sampling temperature (default: 0.2)
        max_tokens: Maximum tokens to generate (default: 4096)
        stream: Whether to stream the response (default: False)
    
    Returns:
        str: The content of the assistant's response
    
    Raises:
        RuntimeError: If LM Studio is not running, model not loaded, or invalid response
    """
    if stream:
        raise NotImplementedError("Streaming is not yet implemented for LM Studio")
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{LMSTUDIO_API_BASE}/chat/completions",
                json=payload
            )
            
            if resp.status_code == 200:
                data = resp.json()
                
                # Validate response structure
                if "choices" not in data or not data["choices"]:
                    raise RuntimeError("LM Studio returned invalid response: missing 'choices' field")
                
                choice = data["choices"][0]
                if "message" not in choice:
                    raise RuntimeError("LM Studio returned invalid response: missing 'message' field")
                
                if "content" not in choice["message"]:
                    raise RuntimeError("LM Studio returned invalid response: missing 'content' field")
                
                return choice["message"]["content"]
            
            elif resp.status_code in (502, 503, 504):
                raise RuntimeError("LM Studio server is unavailable. Please ensure LM Studio is running and the model is loaded.")
            
            elif resp.status_code == 404:
                raise RuntimeError(f"LM Studio model '{model}' not found. Please load the model in LM Studio.")
            
            elif resp.status_code == 400:
                error_msg = resp.text
                if "model" in error_msg.lower() or "not found" in error_msg.lower():
                    raise RuntimeError(f"LM Studio model '{model}' not loaded. Please load the model in LM Studio.")
                raise RuntimeError(f"LM Studio request error: {error_msg}")
            
            else:
                raise RuntimeError(f"LM Studio API error: {resp.status_code} - {resp.text}")
    
    except httpx.ConnectError:
        raise RuntimeError("Cannot connect to LM Studio. Please ensure LM Studio is running on http://localhost:1234")
    
    except httpx.ConnectTimeout:
        raise RuntimeError("Connection to LM Studio timed out. Please check if LM Studio is running.")
    
    except httpx.ReadTimeout:
        raise RuntimeError("LM Studio request timed out. The model may be processing a large request.")
    
    except httpx.NetworkError as e:
        raise RuntimeError(f"Network error connecting to LM Studio: {str(e)}")
    
    except Exception as e:
        if isinstance(e, RuntimeError):
            raise
        raise RuntimeError(f"Error communicating with LM Studio: {str(e)}")


async def ask_llm_stream(
    messages: List[Dict[str, str]],
    model: str = LMSTUDIO_DEFAULT_MODEL,
    temperature: float = 0.2,
    max_tokens: int = 4096
) -> AsyncGenerator[str, None]:
    """
    Stream messages to LM Studio REST API and yield tokens as they arrive.
    
    Args:
        messages: List of message dicts with "role" and "content" keys
        model: Model name (defaults to mistral-7b-instruct-v0.3-q6_k)
        temperature: Sampling temperature (default: 0.2)
        max_tokens: Maximum tokens to generate (default: 4096)
    
    Yields:
        str: Partial tokens as they arrive from LM Studio
    
    Raises:
        RuntimeError: If LM Studio is not running, model not loaded, or invalid response
    """
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True
    }
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{LMSTUDIO_API_BASE}/chat/completions",
                json=payload
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    if response.status_code in (502, 503, 504):
                        raise RuntimeError("LM Studio server is unavailable. Please ensure LM Studio is running and the model is loaded.")
                    elif response.status_code == 404:
                        raise RuntimeError(f"LM Studio model '{model}' not found. Please load the model in LM Studio.")
                    elif response.status_code == 400:
                        error_msg = error_text.decode() if error_text else "Bad request"
                        if "model" in error_msg.lower() or "not found" in error_msg.lower():
                            raise RuntimeError(f"LM Studio model '{model}' not loaded. Please load the model in LM Studio.")
                        raise RuntimeError(f"LM Studio request error: {error_msg}")
                    else:
                        raise RuntimeError(f"LM Studio API error: {response.status_code} - {error_text.decode() if error_text else 'Unknown error'}")
                
                # Process streaming response
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    # LM Studio uses SSE format: "data: {...}" or "data: [DONE]"
                    if line.startswith("data: "):
                        chunk = line[6:].strip()  # Remove "data: " prefix
                        
                        if chunk == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(chunk)
                            
                            # Extract delta content from response
                            if "choices" in data and len(data["choices"]) > 0:
                                choice = data["choices"][0]
                                if "delta" in choice:
                                    delta = choice["delta"]
                                    if "content" in delta:
                                        content = delta["content"]
                                        if content:
                                            yield content
                        except json.JSONDecodeError:
                            # Skip invalid JSON lines
                            logger.debug(f"Skipping invalid JSON line: {chunk[:50]}")
                            continue
                        except Exception as e:
                            logger.warning(f"Error parsing stream chunk: {str(e)}")
                            continue
    
    except httpx.ConnectError:
        raise RuntimeError("Cannot connect to LM Studio. Please ensure LM Studio is running on http://localhost:1234")
    
    except httpx.ConnectTimeout:
        raise RuntimeError("Connection to LM Studio timed out. Please check if LM Studio is running.")
    
    except httpx.ReadTimeout:
        raise RuntimeError("LM Studio request timed out. The model may be processing a large request.")
    
    except httpx.NetworkError as e:
        raise RuntimeError(f"Network error connecting to LM Studio: {str(e)}")
    
    except Exception as e:
        if isinstance(e, RuntimeError):
            raise
        raise RuntimeError(f"Error communicating with LM Studio: {str(e)}")


# Singleton client class for backward compatibility with existing code
class LMStudioClient:
    """Client class that wraps ask_llm for compatibility with existing agent code."""
    
    def __init__(self, api_base: str = LMSTUDIO_API_BASE, model: str = LMSTUDIO_DEFAULT_MODEL):
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.default_max_tokens = getattr(settings, "LMSTUDIO_MAX_TOKENS", 4096)
        self.default_temperature = getattr(settings, "LMSTUDIO_TEMPERATURE", 0.2)
    
    async def ask_llm(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Send messages to LM Studio and return the response.
        
        Args:
            messages: List of message dicts with "role" and "content" keys
            model: Model name (optional, uses default if not provided)
            max_tokens: Maximum tokens (optional, uses default if not provided)
            temperature: Sampling temperature (optional, uses default if not provided)
        
        Returns:
            str: The content of the assistant's response
        """
        return await ask_llm(
            messages=messages,
            model=model or self.model,
            temperature=temperature if temperature is not None else self.default_temperature,
            max_tokens=max_tokens if max_tokens is not None else self.default_max_tokens,
            stream=False
        )
    
    async def stream_llm(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream messages from LM Studio and yield tokens as they arrive.
        
        Args:
            messages: List of message dicts with "role" and "content" keys
            model: Model name (optional, uses default if not provided)
            max_tokens: Maximum tokens (optional, uses default if not provided)
            temperature: Sampling temperature (optional, uses default if not provided)
        
        Yields:
            str: Partial tokens as they arrive from LM Studio
        
        Raises:
            RuntimeError: If LM Studio is not running, model not loaded, or connection fails
        """
        async for token in ask_llm_stream(
            messages=messages,
            model=model or self.model,
            temperature=temperature if temperature is not None else self.default_temperature,
            max_tokens=max_tokens if max_tokens is not None else self.default_max_tokens
        ):
            yield token


# Singleton instance for import compatibility
lmstudio_client = LMStudioClient()

