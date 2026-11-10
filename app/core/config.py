from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "URL Shortener API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    BASE_URL: str = "http://localhost:8000"

    # PostgreSQL Connection String (supports postgresql+asyncpg:// or sqlite+aiosqlite://)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/urlshortener"

    # Redis Connection String
    REDIS_URL: str = "redis://localhost:6379/0"

    # Cache TTL for URLs in seconds (default 24 hours)
    CACHE_TTL_SECONDS: int = 86400

    # CORS
    ALLOWED_ORIGINS: Union[str, List[str]] = "*"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_async_db_url(cls, v: str) -> str:
        """
        Ensures the database URL uses the asyncpg driver when postgresql/postgres is supplied.
        Handles provider formats (Render/Neon/Supabase often supply 'postgres://' or 'postgresql://').
        """
        if not v:
            return v
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("BASE_URL", mode="after")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
