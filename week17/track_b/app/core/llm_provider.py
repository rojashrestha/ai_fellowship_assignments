import json
import logging
import re
from typing import Dict, Any, Optional, List, Type

try:
    from pydantic import BaseModel
except ImportError:
    class BaseModel:
        pass

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

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            config = types.GenerateContentConfig(
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_tokens,
                system_instruction=system_prompt if system_prompt else None
            )
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )
            return response.text or ""
        except Exception as e:
            err_msg = str(e).lower()
            if "quota" in err_msg or "rate" in err_msg or "429" in err_msg:
                raise LLMRateLimitError(f"Gemini Rate Limit Exceeded: {e}")
            elif "connection" in err_msg or "timeout" in err_msg or "503" in err_msg:
                raise LLMServiceUnavailableError(f"Gemini Service Unavailable: {e}")
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
        combined = (prompt + " " + (system_prompt or "")).lower()

        # 1. Verifier Critique Agent simulation
        if "verification agent" in combined or "candidate answer to verify" in combined:
            return json.dumps({
                "passed": True,
                "score": 0.96,
                "critique": "Candidate answer is logically consistent and backed by evidence citations or verified arithmetic.",
                "unsupported_claims": [],
                "recommended_action": "accept"
            })

        # 2. Agentic Loop ReAct Simulation
        if "operating protocol" in combined or "action" in combined or "trajectory" in combined:
            p_low = prompt.lower()
            has_steps = "step 1:" in p_low or "trajectory so far:\nstep" in p_low

            if not has_steps:
                # First step: Decide initial tool call based on user query intent in prompt
                if "sqrt(144)" in p_low or ("calculate" in p_low and "144" in p_low):
                    return json.dumps({
                        "thought": "Query requires arithmetic calculation of sqrt(144) + 2**8. Calling calculate tool.",
                        "action": {"tool_name": "calculate", "arguments": {"expression": "sqrt(144) + 2**8"}},
                        "facts_to_record": ["Evaluated arithmetic for sqrt(144) + 2**8"]
                    })
                elif "25 * 40" in p_low or ("calculate" in p_low and "40" in p_low):
                    return json.dumps({
                        "thought": "Query requires computing 25 * 40 and identifying API framework. Calling calculate.",
                        "action": {"tool_name": "calculate", "arguments": {"expression": "25 * 40"}},
                        "facts_to_record": ["Evaluated arithmetic for 25 * 40"]
                    })
                elif re.search(r'\b(date|time|today)\b', p_low) and "news" not in p_low and "update" not in p_low:
                    return json.dumps({
                        "thought": "Query requests current date and time. Calling get_current_datetime.",
                        "action": {"tool_name": "get_current_datetime", "arguments": {}},
                        "facts_to_record": ["Inspecting system datetime"]
                    })
                elif any(w in p_low for w in ["vector database", "embedding model", "architecture", "deployment docs"]):
                    return json.dumps({
                        "thought": "Query pertains to internal architectural documentation. Querying internal vector store.",
                        "action": {"tool_name": "query_knowledge_base", "arguments": {"query": "vector database embedding model architecture"}},
                        "facts_to_record": ["Retrieved internal RAG architectural chunks"]
                    })
                elif any(w in p_low for w in ["cross_source_fact_checking", "skill"]):
                    return json.dumps({
                        "thought": "Progressive disclosure needed: loading skill instructions for cross_source_fact_checking.",
                        "action": {"tool_name": "load_skill_instructions", "arguments": {"skill_name": "cross_source_fact_checking"}},
                        "facts_to_record": ["Loaded cross_source_fact_checking skill"]
                    })
                elif any(w in p_low for w in ["vllm", "search the web", "search web", "latest ai news"]):
                    return json.dumps({
                        "thought": "External information required. Performing web search.",
                        "action": {"tool_name": "search_web", "arguments": {"query": "vLLM high-throughput serving features"}},
                        "facts_to_record": ["Queried external web evidence"]
                    })
                elif any(w in p_low for w in ["yesterday", "the thing we talked about"]):
                    return json.dumps({
                        "thought": "The query 'the thing we talked about yesterday' is underspecified. Requesting user clarification.",
                        "action": {"tool_name": "ask_user_clarification", "arguments": {"question": "Could you please specify which topic or project from yesterday you are referring to?"}},
                        "facts_to_record": []
                    })
                else:
                    return json.dumps({
                        "thought": "Direct analytical reasoning is sufficient for this query.",
                        "action": {"tool_name": "finish", "arguments": {"answer": "Asynchronous concurrency is beneficial for I/O-bound web services with LLMs because async event loops handle concurrent requests without blocking worker threads, significantly improving throughput and reducing latency."}},
                        "facts_to_record": ["Async concurrency optimizes I/O bound LLM streaming"]
                    })
            else:
                # Subsequent step: Synthesize final answer based on observations
                if any(w in p_low for w in ["failed", "error", "corrupt", "unavailable"]):
                    return json.dumps({
                        "thought": "Tool execution encountered a simulated failure or offline service. Gracefully reporting limitation to user.",
                        "action": {"tool_name": "finish", "arguments": {"answer": "I attempted to retrieve this information, but the requested tool service is temporarily offline, unavailable, or returned an error. I cannot produce a verified response without reliable evidence."}},
                        "facts_to_record": ["Handled tool fault gracefully"]
                    })

                if "25 * 40" in p_low or "1000" in p_low:
                    ans = "The backend API is powered by FastAPI, and the calculation 25 * 40 equals 1000."
                elif "144" in p_low or "268" in p_low:
                    ans = "Based on verified calculation: sqrt(144) + 2**8 = 12 + 256 = 268."
                elif "iso_format" in p_low or "date/time" in p_low or "day_of_week" in p_low:
                    ans = "The current system date and time have been retrieved and verified."
                elif "chromadb" in p_low or "all-minilm" in p_low or "vector database" in p_low:
                    ans = "According to the verified documentation, the AI Assistant architecture utilizes ChromaDB as its vector database and all-MiniLM-L6-v2 as its dense embedding model."
                elif "vllm" in p_low or "pagedattention" in p_low:
                    ans = "vLLM achieves high-throughput LLM serving via PagedAttention and continuous batching algorithms."
                elif "skill" in p_low or "fact_checking" in p_low:
                    ans = "The cross_source_fact_checking skill has been loaded and its step-by-step verification guidelines have been applied."
                else:
                    ans = "Verified synthesis completed using retrieved observations and evidence."

                return json.dumps({
                    "thought": "Observations have been validated against requirements. Concluding with verified final answer.",
                    "action": {"tool_name": "finish", "arguments": {"answer": ans}},
                    "facts_to_record": ["Final answer corroborated"]
                })

        # 3. Extraction schema fallback
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
