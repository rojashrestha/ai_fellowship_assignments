import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    class BaseSettings:
        def __init__(self):
            for attr in dir(self.__class__):
                if attr.isupper():
                    val = os.environ.get(attr, getattr(self.__class__, attr))
                    setattr(self, attr, val)
    class SettingsConfigDict:
        def __init__(self, **kwargs):
            pass


class Settings(BaseSettings):
    # LLM API Keys
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Providers & Models
    PRIMARY_PROVIDER: str = "gemini"  # "gemini", "openai", "vllm", "mock"
    FALLBACK_PROVIDER: Optional[str] = "openai"

    GEMINI_MODEL: str = "gemini-2.5-flash"
    OPENAI_MODEL: str = "gpt-4o-mini"
    VLLM_MODEL: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    VLLM_BASE_URL: str = "http://localhost:8000/v1"

    # Generation Parameters
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_TOP_P: float = 0.9
    DEFAULT_MAX_TOKENS: int = 1024

    # Reliability & Resilience
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_BACKOFF_BASE_SECONDS: float = 1.0

    # Caching
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 3600

    # RAG Settings
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma_db"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
