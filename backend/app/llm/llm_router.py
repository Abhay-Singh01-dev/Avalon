"""
Hybrid Dual-Layer LLM Router

Hospital-Grade LLM Routing for Pilot Deployment

This module provides intelligent routing between local (Mistral-7B) and cloud (Claude/GPT) LLMs.
Currently, cloud LLMs are disabled via feature flag, but the infrastructure is ready for activation.

Architecture:
- Local: Mistral-7B via LM Studio (always preferred)
- Cloud: Claude/GPT (placeholder, not active)

Routing Logic:
- PHI detection → Local only (MANDATORY - never cloud)
- Deep synthesis/20+ citations → Cloud (if enabled)
- Default → Local

PILOT REQUIREMENTS:
- All PHI queries MUST use local model
- No cloud requests allowed during pilot
- Full audit trail of routing decisions
"""

import logging
import httpx
import json
from typing import List, Dict, Optional, AsyncGenerator, Tuple, Any
from enum import Enum

from app.config import settings
from app.llm.lmstudio_client import ask_llm, ask_llm_stream
from app.utils.phi_detector import phi_detector, PHIDetectionResult

logger = logging.getLogger(__name__)


class LLMEngine(str, Enum):
    """Supported LLM engines"""
    LOCAL = "local"
    CLOUD = "cloud"


class CloudProvider(str, Enum):
    """Supported cloud providers"""
    CLAUDE = "claude"
    GPT = "gpt"


class LLMRouter:
    """
    Intelligent LLM routing layer for hybrid local/cloud architecture.
    
    Routes requests between local Mistral-7B and cloud models based on:
    - Prompt complexity
    - PHI detection
    - Feature flags
    - Model capabilities
    """
    
    def __init__(self):
        """Initialize LLM Router with configuration from settings."""
        # Feature flags
        self.use_cloud = getattr(settings, "CLOUD_ENABLED", False)
        self.cloud_provider = getattr(settings, "CLOUD_PROVIDER", "claude")
        
        # Cloud API configuration (placeholders)
        self.cloud_api_key = getattr(settings, "CLOUD_API_KEY", "")
        self.fake_cloud_url = "http://cloud_not_enabled_yet"
        
        # Local LLM configuration
        self.local_model = getattr(settings, "LMSTUDIO_MODEL_NAME", "mistral-7b-instruct-v0.2")
        self.local_base_url = "http://localhost:1234"
        
        logger.info(f"LLMRouter initialized - Cloud: {self.use_cloud}, Provider: {self.cloud_provider}")
    
    async def choose_engine(self, prompt: str, mode: str = "simple") -> Dict[str, Any]:
        """
        Decide which LLM engine to use based on prompt characteristics.
        
        PILOT REQUIREMENT: All PHI queries MUST use local model.
        
        Args:
            prompt: User's query text
            mode: Chat mode (patient, research, document, table, safety, simple)
        
        Returns:
            Dict with:
                - engine: "local" or "cloud"
                - reason: Explanation for engine choice
                - provider: Specific provider (mistral, claude, gpt)
                - phi_detected: Whether PHI was detected
                - phi_details: PHI detection details (if PHI found)
        """
        prompt_lower = prompt.lower()
        
        # RULE 1: PHI Detection - Always use local (CRITICAL FOR PILOT)
        phi_result = self.detect_phi_detailed(prompt)
        
        if phi_result.contains_phi:
            logger.warning(
                f"[PHI_ROUTING] PHI detected - ENFORCING LOCAL-ONLY routing. "
                f"Types: {[t.value for t in phi_result.phi_types]}"
            )
            return {
                "engine": LLMEngine.LOCAL,
                "reason": f"⚠️ PHI DETECTED ({phi_result.confidence:.0%} confidence) - LOCAL model enforced",
                "provider": "mistral-7b",
                "phi_detected": True,
                "phi_details": phi_result.to_dict()
            }
        
        # RULE 2: Check if cloud is even enabled
        if not self.use_cloud:
            return {
                "engine": LLMEngine.LOCAL,
                "reason": "Cloud disabled - using local Mistral-7B",
                "provider": "mistral-7b"
            }
        
        # RULE 3: Mode-based routing
        # Always local for these modes:
        local_modes = ["patient", "safety", "simple", "table", "document"]
        if mode.lower() in local_modes:
            return {
                "engine": LLMEngine.LOCAL,
                "reason": f"{mode.upper()} MODE - optimized for local processing",
                "provider": "mistral-7b"
            }
        
        # RULE 4: Deep synthesis detection (potential cloud candidate)
        if mode.lower() == "research":
            # Check for deep synthesis indicators
            deep_synthesis_keywords = [
                "comprehensive analysis",
                "full landscape",
                "20+ citations",
                "deep dive",
                "extensive research",
                "multi-year",
                "cross-reference",
                "systematic review"
            ]
            
            requires_deep_synthesis = any(kw in prompt_lower for kw in deep_synthesis_keywords)
            
            # Check prompt length (very long prompts might benefit from cloud)
            is_very_long = len(prompt.split()) > 100
            
            if requires_deep_synthesis or is_very_long:
                # Cloud would be preferred, but check if enabled
                if self.use_cloud:
                    return {
                        "engine": LLMEngine.CLOUD,
                        "reason": "Deep synthesis required - routing to cloud for advanced reasoning",
                        "provider": self.cloud_provider
                    }
                else:
                    return {
                        "engine": LLMEngine.LOCAL,
                        "reason": "Deep synthesis needed but cloud disabled - using local Mistral-7B",
                        "provider": "mistral-7b"
                    }
        
        # RULE 5: Default to local
        return {
            "engine": LLMEngine.LOCAL,
            "reason": "Standard query - using local Mistral-7B",
            "provider": "mistral-7b"
        }
    
    def _contains_phi(self, text: str) -> bool:
        """
        Detect Protected Health Information (PHI) in text using comprehensive detector.
        
        Uses the hospital-grade PHI detector which checks for:
        - Patient names (including placeholders like John Doe)
        - Medical record numbers (MRN patterns)
        - Social Security Numbers
        - Dates of birth
        - Phone numbers
        - Email addresses
        - Physical addresses
        - Clinical measurements with patient context
        - Clinical notes patterns (HPI, CC, PMH, etc.)
        
        Returns:
            bool: True if PHI is detected
        """
        result = phi_detector.detect(text)
        
        if result.contains_phi:
            logger.warning(
                f"[PHI_ROUTER] PHI detected - Types: {[t.value for t in result.phi_types]}, "
                f"Confidence: {result.confidence:.2f}"
            )
        
        return result.contains_phi
    
    def detect_phi_detailed(self, text: str) -> PHIDetectionResult:
        """
        Get detailed PHI detection result for audit and timeline events.
        
        Args:
            text: Text to analyze
            
        Returns:
            PHIDetectionResult with full details
        """
        return phi_detector.detect(text)
    
    async def ask_local(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> str:
        """
        Send request to local Mistral-7B via LM Studio.
        
        PILOT: Includes graceful error handling for small model limitations.
        
        Args:
            messages: Chat messages in OpenAI format
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            str: Model response (or graceful fallback message)
        """
        try:
            response = await ask_llm(
                messages=messages,
                model=self.local_model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            # Check for empty or very short responses (model limitation)
            if not response or len(response.strip()) < 10:
                logger.warning("[LLM_LOCAL] Model returned very short response - may indicate limitations")
                return self._get_graceful_fallback_response(messages)
            
            return response
            
        except RuntimeError as e:
            error_msg = str(e)
            logger.error(f"[LLM_LOCAL] Runtime error: {error_msg}")
            
            # Check for common recoverable errors
            if "timeout" in error_msg.lower():
                return self._get_timeout_fallback_response()
            elif "not running" in error_msg.lower() or "cannot connect" in error_msg.lower():
                return self._get_connection_error_response()
            else:
                return self._get_graceful_fallback_response(messages)
                
        except Exception as e:
            logger.error(f"[LLM_LOCAL] Unexpected error: {str(e)}")
            return self._get_graceful_fallback_response(messages)
    
    def _get_graceful_fallback_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a graceful fallback response when the model cannot complete the request.
        
        PILOT: Ensures pipeline continues even with model limitations.
        """
        # Try to extract the user's question for context
        user_query = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_query = msg.get("content", "")[:100]
                break
        
        return (
            "I apologize, but I'm currently unable to generate a complete response for this query. "
            "This may be due to the complexity of the request or temporary model limitations.\n\n"
            "**What you can try:**\n"
            "- Simplify your question\n"
            "- Break it into smaller parts\n"
            "- Ask about a specific aspect\n\n"
            "*The system is using local AI for privacy protection. Some complex analyses may require more processing time.*"
        )
    
    def _get_timeout_fallback_response(self) -> str:
        """Response for timeout errors."""
        return (
            "The analysis is taking longer than expected. This happens with complex pharmaceutical queries.\n\n"
            "**Suggestions:**\n"
            "- Try a more focused question\n"
            "- Ask about one drug or disease at a time\n"
            "- Request a summary instead of detailed analysis\n\n"
            "*Your query was processed locally for privacy protection.*"
        )
    
    def _get_connection_error_response(self) -> str:
        """Response for LM Studio connection errors."""
        return (
            "⚠️ **Local AI Model Unavailable**\n\n"
            "The local AI model (LM Studio) is not currently running. "
            "Please ensure LM Studio is started and a model is loaded.\n\n"
            "**To fix:**\n"
            "1. Open LM Studio application\n"
            "2. Load the Mistral-7B model\n"
            "3. Start the local server (http://localhost:1234)\n"
            "4. Try your query again"
        )
    
    async def ask_local_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> AsyncGenerator[str, None]:
        """
        Stream response from local Mistral-7B via LM Studio.
        
        Args:
            messages: Chat messages in OpenAI format
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Yields:
            str: Response tokens
        """
        try:
            async for token in ask_llm_stream(
                messages=messages,
                model=self.local_model,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                yield token
        except Exception as e:
            logger.error(f"Local LLM streaming error: {str(e)}")
            raise RuntimeError(f"Local LLM (Mistral-7B) streaming error: {str(e)}")
    
    async def ask_cloud(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 8000
    ) -> str:
        """
        Send request to cloud LLM (Claude/GPT) - PLACEHOLDER ONLY.
        
        This function is NOT active. It returns an error indicating cloud is disabled.
        Infrastructure is ready for future activation.
        
        Args:
            messages: Chat messages in OpenAI format
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            str: Error message (cloud disabled)
        """
        if not self.use_cloud:
            error_msg = {
                "error": "Cloud LLM disabled",
                "message": "Cloud models (Claude/GPT) are not enabled. Set CLOUD_ENABLED=true to activate.",
                "provider": self.cloud_provider,
                "fallback": "Using local Mistral-7B instead"
            }
            logger.warning("Cloud LLM requested but disabled")
            return json.dumps(error_msg, indent=2)
        
        # Placeholder for future cloud integration
        if self.cloud_provider == CloudProvider.CLAUDE:
            return await self._ask_claude(messages, temperature, max_tokens)
        elif self.cloud_provider == CloudProvider.GPT:
            return await self._ask_gpt(messages, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown cloud provider: {self.cloud_provider}")
    
    async def _ask_claude(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        PLACEHOLDER: Send request to Claude API.
        
        Not active. Returns error message.
        Ready for activation when CLOUD_ENABLED=true.
        """
        if not self.cloud_api_key:
            return json.dumps({
                "error": "Cloud disabled",
                "message": "Claude API key not configured"
            })
        
        # Placeholder implementation
        logger.info(f"Would call Claude at: {self.fake_cloud_url}")
        
        return json.dumps({
            "error": "Cloud disabled",
            "message": "Claude integration not yet active",
            "endpoint": self.fake_cloud_url,
            "status": "infrastructure ready"
        })
    
    async def _ask_gpt(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        PLACEHOLDER: Send request to GPT API.
        
        Not active. Returns error message.
        Ready for activation when CLOUD_ENABLED=true.
        """
        if not self.cloud_api_key:
            return json.dumps({
                "error": "Cloud disabled",
                "message": "GPT API key not configured"
            })
        
        # Placeholder implementation
        logger.info(f"Would call GPT at: {self.fake_cloud_url}")
        
        return json.dumps({
            "error": "Cloud disabled",
            "message": "GPT integration not yet active",
            "endpoint": self.fake_cloud_url,
            "status": "infrastructure ready"
        })
    
    async def ask(
        self,
        messages: List[Dict[str, str]],
        mode: str = "simple",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """
        Unified interface - automatically chooses engine and sends request.
        
        Args:
            messages: Chat messages in OpenAI format
            mode: Chat mode (patient, research, document, etc.)
            temperature: Sampling temperature (optional)
            max_tokens: Maximum tokens (optional)
            stream: Whether to stream response
        
        Returns:
            str: Model response
        """
        # Get prompt from messages
        prompt = messages[-1]["content"] if messages else ""
        
        # Choose engine
        engine_choice = await self.choose_engine(prompt, mode)
        
        logger.info(f"LLM Routing: {engine_choice['engine']} - {engine_choice['reason']}")
        
        # Route to appropriate engine
        if engine_choice["engine"] == LLMEngine.LOCAL:
            temp = temperature if temperature is not None else 0.2
            tokens = max_tokens if max_tokens is not None else 4096
            
            if stream:
                # Return generator for streaming
                return self.ask_local_stream(messages, temp, tokens)
            else:
                return await self.ask_local(messages, temp, tokens)
        
        elif engine_choice["engine"] == LLMEngine.CLOUD:
            temp = temperature if temperature is not None else 0.7
            tokens = max_tokens if max_tokens is not None else 8000
            
            # Cloud not active - fallback to local
            logger.warning("Cloud requested but not active - falling back to local")
            return await self.ask_local(messages, 0.2, 4096)
        
        else:
            raise ValueError(f"Unknown engine: {engine_choice['engine']}")


# Singleton instance
llm_router = LLMRouter()


# Utility functions for backward compatibility
async def route_llm_request(
    prompt: str,
    mode: str = "simple",
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Helper function to route LLM requests with automatic engine selection.
    
    Args:
        prompt: User's query
        mode: Chat mode
        system_prompt: Optional system prompt
        temperature: Optional temperature
        max_tokens: Optional max tokens
    
    Returns:
        Tuple of (response, engine_info)
    """
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": prompt})
    
    # Get engine choice
    engine_info = await llm_router.choose_engine(prompt, mode)
    
    # Get response
    response = await llm_router.ask(
        messages=messages,
        mode=mode,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False
    )
    
    return response, engine_info
