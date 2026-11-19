"""Configuration module using Pydantic Settings."""

import os
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM API Keys
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    @field_validator("GEMINI_API_KEY", "OPENAI_API_KEY", mode="before")
    @classmethod
    def clean_quotes(cls, v):
        if isinstance(v, str):
            return v.strip("\"' ")
        return v

    # Providers & Models
    PRIMARY_PROVIDER: str = "gemini"  # "gemini", "openai", "vllm", "mock"
    FALLBACK_PROVIDER: Optional[str] = "openai"

    GEMINI_MODEL: str = "gemini-1.5-flash"
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
