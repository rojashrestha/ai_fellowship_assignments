import time
import logging
import asyncio
from typing import Callable, Any, Dict, Optional, Tuple

try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential_jitter,
        retry_if_exception_type,
        before_sleep_log
    )
except ImportError:
    def retry(*args, **kwargs):
        def decorator(f):
            return f
        return decorator
    def stop_after_attempt(n): return None
    def wait_exponential_jitter(*args, **kwargs): return None
    def retry_if_exception_type(*args, **kwargs): return None
    def before_sleep_log(*args, **kwargs): return None

try:
    from fastapi import HTTPException, status
except ImportError:
    class HTTPException(Exception):
        def __init__(self, status_code=500, detail=""):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)
    class status:
        HTTP_429_TOO_MANY_REQUESTS = 429
        HTTP_503_SERVICE_UNAVAILABLE = 503
        HTTP_502_BAD_GATEWAY = 502

from app.config import settings

logger = logging.getLogger("ai_assistant.resilience")
logging.basicConfig(level=logging.INFO)


# ---------------------------------------------------------
# Rate Limiter (Token Bucket Algorithm)
# ---------------------------------------------------------
class TokenBucketRateLimiter:
    """Thread-safe Token Bucket Rate Limiter for request throttling."""

    def __init__(self, requests_per_minute: int = settings.RATE_LIMIT_REQUESTS_PER_MINUTE):
        self.capacity = float(requests_per_minute)
        self.tokens = self.capacity
        self.fill_rate = self.capacity / 60.0  # tokens added per second
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """Attempt to consume 1 token. Returns True if permitted, False otherwise."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)
            self.last_update = now

            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return True
            return False

    async def check_or_raise(self):
        """Raise HTTP 429 if rate limit is exceeded."""
        allowed = await self.acquire()
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please throttle your requests."
            )


rate_limiter = TokenBucketRateLimiter()


# ---------------------------------------------------------
# Custom Exceptions for LLM & Provider Failures
# ---------------------------------------------------------
class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""
    pass


class LLMRateLimitError(LLMProviderError):
    """Raised when upstream LLM returns 429/quota error."""
    pass


class LLMServiceUnavailableError(LLMProviderError):
    """Raised when upstream LLM service is unreachable or 5xx."""
    pass


# ---------------------------------------------------------
# Retry Decorator with Exponential Backoff + Jitter
# ---------------------------------------------------------
def create_retry_decorator(
    max_attempts: int = settings.RETRY_MAX_ATTEMPTS,
    base_seconds: float = settings.RETRY_BACKOFF_BASE_SECONDS
):
    """Generates a tenacity retry decorator with exponential backoff and randomized jitter."""
    return retry(
        reraise=True,
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential_jitter(
            initial=base_seconds,
            max=10.0,
            jitter=0.5
        ),
        retry=retry_if_exception_type((LLMProviderError, TimeoutError, ConnectionError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )


# ---------------------------------------------------------
# Multi-Provider Fallback Orchestrator
# ---------------------------------------------------------
class FallbackOrchestrator:
    """Executes calls against a primary provider and seamlessly switches to fallback on failure."""

    @staticmethod
    async def execute_with_fallback(
        primary_callable: Callable[..., Any],
        fallback_callable: Optional[Callable[..., Any]],
        *args,
        **kwargs
    ) -> Tuple[Any, str]:
        """
        Executes primary callable. If it fails after all retries, attempts fallback.
        If both fail, provides graceful degradation.
        
        Returns: (result_data, provider_name_used)
        """
        try:
            logger.info("Attempting call via Primary LLM provider...")
            result = await primary_callable(*args, **kwargs)
            return result, "primary"
        except Exception as primary_err:
            logger.error(f"Primary provider failed with error: {primary_err}")
            
            if fallback_callable:
                try:
                    logger.warning("Failing over to Fallback LLM provider...")
                    result = await fallback_callable(*args, **kwargs)
                    return result, "fallback"
                except Exception as fallback_err:
                    logger.critical(f"Fallback provider also failed: {fallback_err}")
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"All LLM providers failed. Primary error: {str(primary_err)}. Fallback error: {str(fallback_err)}"
                    )
            
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Primary LLM provider failed: {str(primary_err)}"
            )
