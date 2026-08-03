"""
Centralized application configuration.

All environment-driven settings live here. No other module should call
os.environ / os.getenv directly — this is the single source of truth,
enforced by convention and code review.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    log_level: str = "INFO"
    site_id: str = "greenhouse-01"

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int = 5432

    secret_key: str
    cors_origins: str = "http://localhost:5173"

    mqtt_host: str
    mqtt_port: int = 1883
    mqtt_username: str
    mqtt_password: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — avoids re-parsing env on every call."""
    return Settings()
