"""
Centralized application configuration.

All values are read from environment variables (or a `.env` file locally).
In AWS, these are injected via ECS task definition `secrets` / `environment`
blocks, backed by AWS Secrets Manager / SSM Parameter Store — never hardcode
credentials here.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "FinGPT Enterprise"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # --- Security / Auth ---
    JWT_SECRET_KEY: str = Field(..., description="HS256 signing secret, injected via Secrets Manager")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Database (RDS Postgres) ---
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "fingpt"
    POSTGRES_PASSWORD: str = "fingpt"
    POSTGRES_DB: str = "fingpt_enterprise"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # --- Redis (ElastiCache) ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Qdrant (self-hosted ECS or Qdrant Cloud) ---
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "fingpt_documents"

    # --- LLM providers ---
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    LLM_MODEL: str = "gpt-4o-mini"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # --- AWS ---
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET_DOCUMENTS: str = "fingpt-enterprise-documents"

    # --- Rate limiting ---
    RATE_LIMIT_PER_MINUTE: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
