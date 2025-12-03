""
Rate limiting implementation using token bucket algorithm.
"""
import time
import asyncio
from typing import Dict, Optional, Tuple, Any
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, detail: str, headers: Optional[Dict[str, str]] = None):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=headers or {}
        )

class TokenBucket:
    """Token bucket rate limiting implementation."""
    
    def __init__(self, rate: float, capacity: int):
        """
        Initialize the token bucket.
        
        Args:
            rate: Tokens added per second
            capacity: Maximum number of tokens in the bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            bool: True if tokens were consumed, False if rate limit exceeded
        """
        async with self._lock:
            now = time.monotonic()
            # Add tokens based on time passed
            time_passed = now - self.last_update
            self.tokens = min(
                self.capacity,
                self.tokens + time_passed * self.rate
            )
            self.last_update = now
            
            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def get_retry_after(self) -> float:
        """Calculate how long to wait before retrying in seconds."""
        return (1.0 - self.tokens) / self.rate if self.rate > 0 else 0

class RateLimiter:
    """Rate limiter with support for multiple scopes and rules."""
    
    def __init__(self):
        self.buckets: Dict[Tuple[str, str], TokenBucket] = {}
        self.rules: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    def add_rule(self, scope: str, rule: Dict[str, Any]) -> None:
        """
        Add a rate limiting rule.
        
        Args:
            scope: Scope name (e.g., 'api', 'auth')
            rule: Dictionary containing 'rate' (tokens/second) and 'capacity' (max tokens)
        """
        self.rules[scope] = rule
    
    async def _get_bucket(self, scope: str, key: str) -> TokenBucket:
        """Get or create a token bucket for the given scope and key."""
        bucket_key = (scope, key)
        
        # Fast path - bucket exists
        if bucket_key in self.buckets:
            return self.buckets[bucket_key]
        
        # Slow path - need to create a new bucket
        async with self._lock:
            # Double-check in case another coroutine created it while we were waiting
            if bucket_key in self.buckets:
                return self.buckets[bucket_key]
            
            # Create new bucket with default rate and capacity
            rule = self.rules.get(scope, {"rate": 1.0, "capacity": 10})
            bucket = TokenBucket(
                rate=rule["rate"],
                capacity=rule["capacity"]
            )
            self.buckets[bucket_key] = bucket
            return bucket
    
    async def check_rate_limit(
        self, 
        scope: str, 
        key: str, 
        cost: int = 1,
        raise_on_failure: bool = True
    ) -> Tuple[bool, Optional[float]]:
        """
        Check if the request is allowed by the rate limiter.
        
        Args:
            scope: Rate limiting scope (e.g., 'api', 'auth')
            key: Unique identifier for the rate limit (e.g., IP, user ID, API key)
            cost: Number of tokens to consume
            raise_on_failure: Whether to raise an exception on rate limit exceeded
            
        Returns:
            Tuple of (allowed, retry_after_seconds)
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded and raise_on_failure is True
        """
        bucket = await self._get_bucket(scope, key)
        allowed = await bucket.consume(cost)
        
        if not allowed and raise_on_failure:
            retry_after = bucket.get_retry_after()
            raise RateLimitExceeded(
                detail=(
                    f"Rate limit exceeded for {scope}. "
                    f"Please try again in {retry_after:.1f} seconds."
                ),
                headers={
                    "X-RateLimit-Limit": str(bucket.capacity),
                    "X-RateLimit-Remaining": str(int(bucket.tokens)),
                    "X-RateLimit-Reset": str(int(time.time() + retry_after)),
                    "Retry-After": str(int(retry_after))
                }
            )
        
        return allowed, bucket.get_retry_after()

# Global rate limiter instance
rate_limiter = RateLimiter()

# Add default rules
rate_limiter.add_rule("api", {"rate": 2.0, "capacity": 30})  # 2 requests per second, burst of 30
rate_limiter.add_rule("auth", {"rate": 0.1, "capacity": 5})  # 1 request every 10 seconds, burst of 5
rate_limiter.add_rule("llm", {"rate": 0.5, "capacity": 15})  # 1 request every 2 seconds, burst of 15

def rate_limit_middleware(scope: str = "api", cost: int = 1):
    """
    FastAPI middleware for rate limiting.
    
    Args:
        scope: Rate limiting scope to use
        cost: Number of tokens to consume per request
    """
    async def middleware(request: Request, call_next):
        # Get client IP (supports proxy headers)
        client_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0] or
            request.headers.get("x-real-ip") or
            request.client.host or "unknown"
        )
        
        # Use API key if available, otherwise use IP
        api_key = request.headers.get("x-api-key")
        rate_limit_key = f"api_key:{api_key}" if api_key else f"ip:{client_ip}"
        
        try:
            # Check rate limit
            allowed, retry_after = await rate_limiter.check_rate_limit(
                scope=scope,
                key=rate_limit_key,
                cost=cost,
                raise_on_failure=True
            )
            
            # Add rate limit headers to response
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Scope"] = scope
            response.headers["X-RateLimit-Limit"] = str(rate_limiter.rules.get(scope, {}).get("capacity", 0))
            
            return response
            
        except RateLimitExceeded as e:
            logger.warning(
                f"Rate limit exceeded for {rate_limit_key} on {request.url.path}: {e.detail}"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": str(e.detail),
                    "retry_after": e.headers.get("Retry-After", 60)
                },
                headers=dict(e.headers)
            )
        
        except Exception as e:
            logger.error(f"Error in rate limiter: {e}", exc_info=True)
            # Don't block the request if rate limiting fails
            return await call_next(request)
    
    return middleware
