"""Multi-provider LLM client supporting Gemini, OpenAI, local vLLM, and Mock for testing."""

import json
import logging
from typing import Dict, Any, Optional, List, Type
from pydantic import BaseModel
import httpx
from app.config import settings
from app.core.resilience import (
    create_retry_decorator,
    LLMProviderError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
    FallbackOrchestrator
)
from app.core.cache import cache

logger = logging.getLogger("ai_assistant.llm_provider")


class BaseLLMClient:
    """Abstract base client for LLM providers."""

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = settings.DEFAULT_TEMPERATURE,
        top_p: float = settings.DEFAULT_TOP_P,
        max_tokens: int = settings.DEFAULT_MAX_TOKENS,
        **kwargs
    ) -> str:
        raise NotImplementedError

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        **kwargs
    ) -> BaseModel:
        raise NotImplementedError


class GeminiClient(BaseLLMClient):
    """Google Gemini Client using google-genai SDK or direct REST."""

    def __init__(self, api_key: Optional[str] = None, model: str = settings.GEMINI_MODEL):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model

    @create_retry_decorator()
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = settings.DEFAULT_TEMPERATURE,
        top_p: float = settings.DEFAULT_TOP_P,
        max_tokens: int = settings.DEFAULT_MAX_TOKENS,
        **kwargs
    ) -> str:
        if not self.api_key:
            raise LLMProviderError("GEMINI_API_KEY is not configured.")

        model_name = self.model or "gemini-1.5-flash"
        if model_name.startswith("models/"):
            model_name = model_name.replace("models/", "")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        body: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "topP": top_p,
                "maxOutputTokens": max_tokens
            }
        }
        if system_prompt:
            body["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        try:
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                # Send key via x-goog-api-key header and query parameter for full support of AQ. keys
                resp = await http_client.post(
                    f"{url}?key={self.api_key}",
                    headers=headers,
                    json=body
                )
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                    return ""

                # If requested model gave 404, fallback to gemini-1.5-flash
                if resp.status_code == 404 and model_name != "gemini-1.5-flash":
                    fallback_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
                    resp2 = await http_client.post(
                        f"{fallback_url}?key={self.api_key}",
                        headers=headers,
                        json=body
                    )
                    if resp2.status_code == 200:
                        data = resp2.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
                        return ""

                error_body = resp.text
                if resp.status_code == 429:
                    raise LLMRateLimitError(f"Gemini Rate Limit (429): {error_body}")
                elif resp.status_code in [500, 502, 503, 504]:
                    raise LLMServiceUnavailableError(f"Gemini Service Unavailable ({resp.status_code}): {error_body}")
                else:
                    raise LLMProviderError(f"Gemini API Error ({resp.status_code}): {error_body}")

        except (LLMRateLimitError, LLMServiceUnavailableError, LLMProviderError):
            raise
        except Exception as e:
            err_msg = str(e).lower()
            if "timeout" in err_msg or "connection" in err_msg:
                raise LLMServiceUnavailableError(f"Gemini Connection Timeout: {e}")
            raise LLMProviderError(f"Gemini generation error: {e}")


class OpenAIClient(BaseLLMClient):
    """OpenAI and OpenAI-compatible (vLLM / Ollama) Client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = settings.OPENAI_MODEL,
        base_url: Optional[str] = None
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY or "dummy_key_for_vllm"
        self.model = model
        self.base_url = base_url

    @create_retry_decorator()
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = settings.DEFAULT_TEMPERATURE,
        top_p: float = settings.DEFAULT_TOP_P,
        max_tokens: int = settings.DEFAULT_MAX_TOKENS,
        **kwargs
    ) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            err_msg = str(e).lower()
            if "429" in err_msg or "rate limit" in err_msg:
                raise LLMRateLimitError(f"OpenAI/vLLM Rate Limit: {e}")
            elif "503" in err_msg or "connection" in err_msg:
                raise LLMServiceUnavailableError(f"OpenAI/vLLM Service Unavailable: {e}")
            raise LLMProviderError(f"OpenAI/vLLM Error: {e}")


class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing and offline development without API keys."""

    def __init__(self, name: str = "mock"):
        self.name = name

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = settings.DEFAULT_TEMPERATURE,
        top_p: float = settings.DEFAULT_TOP_P,
        max_tokens: int = settings.DEFAULT_MAX_TOKENS,
        **kwargs
    ) -> str:
        if "json" in prompt.lower() or (system_prompt and "json" in system_prompt.lower()):
            return json.dumps({
                "summary": f"Synthesized analysis for query: {prompt[:40]}...",
                "key_points": ["Validated data points", "Applied contextual reasoning", "Formulated answer"],
                "entities": [{"name": "AI Assistant", "category": "System"}],
                "sentiment": "positive"
            })
        return f"[MOCK {self.name.upper()}] Response to '{prompt[:60]}' with temp={temperature}, top_p={top_p}."


class LLMService:
    """Unified LLM Service orchestrating providers, fallback, caching, and structured outputs."""

    def __init__(self):
        self.clients: Dict[str, BaseLLMClient] = {
            "gemini": GeminiClient(),
            "openai": OpenAIClient(model=settings.OPENAI_MODEL),
            "vllm": OpenAIClient(
                model=settings.VLLM_MODEL,
                base_url=settings.VLLM_BASE_URL
            ),
            "mock": MockLLMClient("mock-primary"),
            "mock-fallback": MockLLMClient("mock-fallback")
        }

    def _get_client(self, provider_name: str) -> BaseLLMClient:
        return self.clients.get(provider_name.lower(), self.clients["mock"])

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        provider: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Generate response with automated caching, provider execution, and fallback.
        """
        temp = temperature if temperature is not None else settings.DEFAULT_TEMPERATURE
        t_p = top_p if top_p is not None else settings.DEFAULT_TOP_P
        m_tokens = max_tokens if max_tokens is not None else settings.DEFAULT_MAX_TOKENS
        
        primary_name = provider or settings.PRIMARY_PROVIDER
        fallback_name = settings.FALLBACK_PROVIDER

        params = {"temperature": temp, "top_p": t_p, "max_tokens": m_tokens}

        # Check Cache
        if use_cache:
            cached_data = cache.get(prompt, system_prompt, params)
            if cached_data:
                cached_data["cached"] = True
                return cached_data

        primary_client = self._get_client(primary_name)
        fallback_client = self._get_client(fallback_name) if fallback_name else None

        async def _call_primary():
            return await primary_client.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temp,
                top_p=t_p,
                max_tokens=m_tokens
            )

        async def _call_fallback():
            if fallback_client:
                return await fallback_client.generate_text(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temp,
                    top_p=t_p,
                    max_tokens=m_tokens
                )
            raise LLMProviderError("No fallback provider available")

        text, used_provider_tier = await FallbackOrchestrator.execute_with_fallback(
            _call_primary,
            _call_fallback if fallback_client else None
        )

        resolved_provider_name = primary_name if used_provider_tier == "primary" else fallback_name

        result = {
            "text": text,
            "provider": resolved_provider_name,
            "provider_tier": used_provider_tier,
            "cached": False
        }

        # Store in cache
        if use_cache:
            cache.set(prompt, result, system_prompt, params)

        return result


# Global LLM service instance
llm_service = LLMService()
