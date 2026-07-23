"""Application settings, loaded from environment (.env for local dev)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://user_api:user_api@localhost:5432/user_api"

    jwks_url: str
    jwt_issuer: str
    jwt_audience: str

    internal_api_key: str


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
