from functools import lru_cache

from pydantic import ConfigDict, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    DATABASE_URL_SYNC: str = "sqlite:///./app.db"
    CORS_ORIGINS: str = "http://localhost:5173"
    APP_TITLE: str = "Danang Coffee API"
    APP_VERSION: str = "1.0.0"
    CLOUDINARY_CLOUD_NAME: str | None = None
    CLOUDINARY_API_KEY: str | None = None
    CLOUDINARY_API_SECRET: str | None = None

    # Admin Security
    SECRET_KEY: str | None = None

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_and_format_settings(self):
        from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

        # 1. Format DATABASE_URL
        if self.DATABASE_URL:
            db_url = self.DATABASE_URL
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

            parsed = urlparse(db_url)
            if parsed.query:
                params = dict(parse_qsl(parsed.query))
                # Map sslmode to ssl for asyncpg
                if "sslmode" in params and "ssl" not in params:
                    params["ssl"] = params.pop("sslmode")
                elif "sslmode" in params:
                    params.pop("sslmode")

                # Whitelist of query parameters that asyncpg accepts
                asyncpg_safe_params = {
                    "ssl",
                    "timeout",
                    "command_timeout",
                    "statement_cache_size",
                    "max_cached_statement_use_count",
                    "max_cacheable_statement_size",
                    "direct_tls",
                }
                filtered_params = {k: v for k, v in params.items() if k in asyncpg_safe_params}
                new_query = urlencode(filtered_params)
                self.DATABASE_URL = urlunparse(parsed._replace(query=new_query))
            else:
                self.DATABASE_URL = db_url

        # 2. Format DATABASE_URL_SYNC
        if self.DATABASE_URL_SYNC:
            if self.DATABASE_URL_SYNC.startswith("postgres://"):
                self.DATABASE_URL_SYNC = self.DATABASE_URL_SYNC.replace("postgres://", "postgresql://", 1)

        if self.SECRET_KEY:
            return self
        if self.ENVIRONMENT.lower() in {"production", "prod"}:
            raise ValueError("SECRET_KEY must be set when ENVIRONMENT=production")
        self.SECRET_KEY = "dev-secret-key-change-before-production"
        return self


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()


# Backward compatible: existing code imports `settings` directly
settings = get_settings()
