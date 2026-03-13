import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://danang_coffee:danang_coffee_2024@coffee-db:5432/danang_coffee",
    )
    DATABASE_URL_SYNC: str = os.getenv(
        "DATABASE_URL_SYNC",
        "postgresql://danang_coffee:danang_coffee_2024@coffee-db:5432/danang_coffee",
    )
    APP_TITLE: str = "Danang Coffee API"
    APP_VERSION: str = "1.0.0"

    # Admin Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-for-admin-sessions-12345")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
