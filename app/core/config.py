from typing import List, Union
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
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
        Ensures the database URL uses the asyncpg driver and compatible query parameters.
        Handles provider formats (Render/Neon/Supabase often supply 'postgres://' or 'postgresql://' with '?sslmode=require').
        Converts 'sslmode' to 'ssl' because asyncpg expects 'ssl' and rejects 'sslmode'.
        """
        if not v:
            return v
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Sanitize query parameters for asyncpg
        parsed = urlparse(v)
        if "asyncpg" in parsed.scheme:
            query_params = parse_qs(parsed.query)
            cleaned_params = {}
            for key, values in query_params.items():
                val = values[0] if values else ""
                if key == "sslmode":
                    # asyncpg takes 'ssl', not 'sslmode'
                    cleaned_params["ssl"] = val
                elif key in (
                    "ssl",
                    "timeout",
                    "command_timeout",
                    "statement_cache_size",
                    "max_cached_statement_lifetime",
                ):
                    cleaned_params[key] = val
                # Ignore unknown/unsupported params (e.g. channel_binding, endpoint)

            new_query = urlencode(cleaned_params)
            v = urlunparse(parsed._replace(query=new_query))

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
