"""
Retry decorator with exponential backoff for handling transient failures.
"""
import asyncio
import functools
import logging
import random
from typing import Any, Callable, Optional, Type, TypeVar, Union, List, Tuple, Dict, TypeVar, Awaitable, cast
from datetime import datetime, timedelta

# Type variable for generic return types
T = TypeVar('T')

# Configure logging
logger = logging.getLogger(__name__)

class MaxRetriesExceededError(Exception):
    """Raised when the maximum number of retries is exceeded."""
    
    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        self.last_exception = last_exception
        super().__init__(message)

class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 0.1,
        max_delay: float = 30.0,
        jitter: float = 0.2,
        exponential_base: float = 2.0,
        retry_on: Optional[Union[Type[Exception], Tuple[Type[Exception], ...]]] = None,
        retry_if: Optional[Callable[[Exception], bool]] = None,
        on_retry: Optional[Callable[[int, float, Exception], None]] = None,
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of retry attempts (including initial attempt)
            base_delay: Base delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            jitter: Random jitter factor (0.0 to 1.0)
            exponential_base: Base for exponential backoff
            retry_on: Exception type(s) to retry on (default: all exceptions)
            retry_if: Callable that takes an exception and returns whether to retry
            on_retry: Callback function called before each retry (attempt, delay, exception)
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.exponential_base = exponential_base
        self.retry_on = retry_on or (Exception,)
        self.retry_if = retry_if or (lambda _: True)
        self.on_retry = on_retry

    def get_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        # Calculate exponential backoff
        delay = min(
            self.max_delay,
            self.base_delay * (self.exponential_base ** (attempt - 1))
        )
        
        # Add jitter
        if self.jitter > 0:
            delay = delay * (1 - self.jitter + 2 * self.jitter * random.random())
        
        return float(delay)

def retry(
    func: Optional[Callable[..., Awaitable[T]]] = None,
    max_attempts: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 30.0,
    jitter: float = 0.2,
    exponential_base: float = 2.0,
    retry_on: Optional[Union[Type[Exception], Tuple[Type[Exception], ...]]] = None,
    retry_if: Optional[Callable[[Exception], bool]] = None,
    on_retry: Optional[Callable[[int, float, Exception], None]] = None,
) -> Callable[..., Callable[..., Awaitable[T]]]:
    """
    Decorator for adding retry logic to async functions.
    
    Args:
        func: The async function to decorate (automatically passed by decorator syntax)
        max_attempts: Maximum number of retry attempts (including initial attempt)
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        jitter: Random jitter factor (0.0 to 1.0)
        exponential_base: Base for exponential backoff
        retry_on: Exception type(s) to retry on (default: all exceptions)
        retry_if: Callable that takes an exception and returns whether to retry
        on_retry: Callback function called before each retry (attempt, delay, exception)
    
    Returns:
        Decorated function with retry logic
    """
    # Allow both @retry and @retry(...) syntax
    if func is None:
        return lambda f: retry(
            func=f,
            max_attempts=max_attempts,
            base_delay=base_delay,
            max_delay=max_delay,
            jitter=jitter,
            exponential_base=exponential_base,
            retry_on=retry_on,
            retry_if=retry_if,
            on_retry=on_retry,
        )
    
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        jitter=jitter,
        exponential_base=exponential_base,
        retry_on=retry_on,
        retry_if=retry_if or (lambda _: True),
        on_retry=on_retry,
    )
    
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        last_exception = None
        
        for attempt in range(1, config.max_attempts + 1):
            try:
                # Try to call the function
                return await func(*args, **kwargs)
                
            except config.retry_on as e:
                # Check if we should retry this exception
                if not config.retry_if(e):
                    raise
                
                last_exception = e
                
                # If this was the last attempt, break and raise
                if attempt >= config.max_attempts:
                    break
                
                # Calculate delay with backoff and jitter
                delay = config.get_delay(attempt)
                
                # Log the retry
                logger.warning(
                    f"Attempt {attempt}/{config.max_attempts} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                
                # Call the on_retry callback if provided
                if config.on_retry:
                    try:
                        config.on_retry(attempt, delay, e)
                    except Exception as cb_error:
                        logger.error(f"Error in on_retry callback: {cb_error}", exc_info=True)
                
                # Wait before retrying
                await asyncio.sleep(delay)
        
        # If we get here, all retry attempts failed
        error_msg = (
            f"Failed after {config.max_attempts} attempts. "
            f"Last error: {last_exception}"
        )
        raise MaxRetriesExceededError(error_msg, last_exception) from last_exception
    
    return wrapper

def retry_llm_call(
    func: Optional[Callable[..., Awaitable[T]]] = None,
    max_attempts: int = 3,
    base_delay: float = 0.75,
    max_delay: float = 30.0,
    jitter: float = 0.2,
) -> Callable[..., Callable[..., Awaitable[T]]]:
    """
    Pre-configured retry decorator for LLM API calls.
    
    Args:
        func: The async function to decorate
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Base delay between retries in seconds (default: 0.75s)
        max_delay: Maximum delay between retries in seconds (default: 30s)
        jitter: Random jitter factor (default: 0.2)
    
    Returns:
        Decorated function with retry logic
    """
    # Import here to avoid circular imports
    from fastapi import HTTPException
    
    def is_retryable_error(e: Exception) -> bool:
        """Determine if an error is retryable."""
        # Retry on connection errors, timeouts, and rate limits
        error_str = str(e).lower()
        return any(
            msg in error_str
            for msg in [
                'connection',
                'timeout',
                'rate limit',
                'rate_limit',
                'too many requests',
                '429',
                'server error',
                'service unavailable',
                'temporarily unavailable',
            ]
        )
    
    def on_retry(attempt: int, delay: float, exc: Exception) -> None:
        """Log retry attempts."""
        logger.warning(
            f"LLM call attempt {attempt} failed: {exc}. "
            f"Retrying in {delay:.2f}s..."
        )
    
    return retry(
        func=func,
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        jitter=jitter,
        exponential_base=2.0,
        retry_on=(
            ConnectionError,
            TimeoutError,
            HTTPException,
            Exception,  # Catch-all for other exceptions
        ),
        retry_if=is_retryable_error,
        on_retry=on_retry,
    )

def with_retry(
    func: Callable[..., Awaitable[T]],
    *args: Any,
    **kwargs: Any,
) -> Callable[[], Awaitable[T]]:
    """
    Create a retryable coroutine function.
    
    This is useful for passing retryable functions to asyncio.gather().
    
    Example:
        results = await asyncio.gather(
            with_retry(some_function, arg1, arg2, max_attempts=3),
            with_retry(another_function, kwarg1=value, max_attempts=5),
        )
    """
    # Extract retry parameters from kwargs
    retry_kwargs = {}
    retry_params = [
        'max_attempts', 'base_delay', 'max_delay',
        'jitter', 'exponential_base', 'retry_on',
        'retry_if', 'on_retry'
    ]
    
    for param in retry_params:
        if param in kwargs:
            retry_kwargs[param] = kwargs.pop(param)
    
    # Create a retryable version of the function
    retryable_func = retry(func=func, **retry_kwargs)
    
    # Return a coroutine function that calls the retryable function
    async def wrapped() -> T:
        return await retryable_func(*args, **kwargs)
    
    return wrapped
