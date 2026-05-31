"""
AI创作工坊 - Application Configuration

Uses Pydantic Settings for type-safe configuration management.
Supports environment variables, .env files, and defaults.
Demonstrates: Pydantic v2, environment-based config, multi-tenant settings.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ─── App ────────────────────────────────────────────
    app_name: str = "AI创作工坊"
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"

    # ─── Database ───────────────────────────────────────
    database_url: str = "postgresql+asyncpg://ai_workshop:ai_workshop_pass@localhost:5432/ai_workshop"

    # ─── Redis ──────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ─── Vector Store ───────────────────────────────────
    chromadb_host: str = "localhost"
    chromadb_port: int = 8100

    # ─── LLM Providers ─────────────────────────────────
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    local_llm_base_url: str = "http://localhost:8081/v1"
    local_llm_model: str = "local-model"
    llm_provider_priority: str = "openai,anthropic,local"

    # ─── Embedding ──────────────────────────────────────
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # ─── JWT ────────────────────────────────────────────
    jwt_secret_key: str = "change-me-jwt-secret-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # ─── Rate Limiting ──────────────────────────────────
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10

    # ─── Monitoring ─────────────────────────────────────
    prometheus_enabled: bool = True
    otel_exporter_endpoint: str = "http://localhost:4317"
    log_level: str = "INFO"
    log_format: str = "json"

    # ─── CORS ───────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:8080", "http://localhost:3000"]

    # ─── SaaS Billing ──────────────────────────────────
    billing_enabled: bool = True
    token_price_input: float = 0.000015   # per token (USD)
    token_price_output: float = 0.00006   # per token (USD)

    # ─── Fine-tuning ───────────────────────────────────
    wandb_api_key: Optional[str] = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @property
    def provider_list(self) -> list[str]:
        """Parse comma-separated provider priority."""
        return [p.strip() for p in self.llm_provider_priority.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings (singleton pattern)."""
    return Settings()
