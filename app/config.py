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
        # Convert standard postgresql:// or postgres:// to postgresql+asyncpg:// if needed
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
        elif self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

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
