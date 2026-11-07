from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SEEKORA_", env_file=".env", extra="ignore", case_sensitive=False
    )

    app_name: str = "Seekora"
    env: str = "development"
    database_url: str = "postgresql+psycopg://seekora:seekora@localhost:5432/seekora"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:3000"
    crawler_user_agent: str = "SeekoraBot/0.1 (+http://localhost:3000/about)"
    crawl_min_delay_seconds: float = Field(default=1.0, ge=0.0)
    crawl_timeout_seconds: float = Field(default=12.0, gt=0.0, le=60.0)
    max_response_bytes: int = Field(default=5_000_000, ge=1024, le=20_000_000)
    max_document_characters: int = Field(default=500_000, ge=1000, le=2_000_000)
    log_level: str = "INFO"
    demo_mode: bool = False
    admin_api_key: SecretStr = SecretStr("seekora-dev-key-change-me")
    rate_limit_enabled: bool = True
    rate_limit_requests: int = Field(default=120, ge=1, le=10_000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    rag_provider: Literal["extractive", "openai-compatible"] = "extractive"
    rag_model: str = "local-extractive-v1"
    rag_base_url: str = "https://api.openai.com/v1"
    rag_api_key: SecretStr | None = None
    answer_max_sources: int = Field(default=4, ge=1, le=10)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        admin_key = self.admin_api_key.get_secret_value()
        if self.env == "production" and (
            admin_key.startswith("seekora-dev-key") or admin_key.startswith("replace-with")
        ):
            raise ValueError("SEEKORA_ADMIN_API_KEY must be replaced in production")
        if self.rag_provider == "openai-compatible" and (
            self.rag_api_key is None or not self.rag_api_key.get_secret_value()
        ):
            raise ValueError("SEEKORA_RAG_API_KEY is required for the configured RAG provider")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
