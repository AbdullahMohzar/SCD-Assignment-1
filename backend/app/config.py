from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    PORT: int = 8000

    # PostgreSQL Database
    DATABASE_URL: str = "postgresql+asyncpg://civicpulse_user:civicpulse_secure_password_replace_in_prod@database:5432/civicpulse"
    SYNC_DATABASE_URL: str = "postgresql://civicpulse_user:civicpulse_secure_password_replace_in_prod@database:5432/civicpulse"

    # Redis Cache & Distributed Rate Limiter
    REDIS_URL: str = "redis://:civicpulse_redis_secret_replace_in_prod@cache:6379/0"
    RATE_LIMIT_PER_MINUTE: int = 20

    # Triage Configuration
    # Options: llm:groq | llm:gemini | llm:ollama | rules | simulated
    TRIAGE_PROVIDER: str = "simulated"
    TRIAGE_TIMEOUT_SECONDS: float = 10.0
    TRIAGE_CACHE_TTL_SECONDS: int = 86400

    # Hosted LLM APIs
    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Local Ollama
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
