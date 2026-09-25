from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings read from environment variables, or from a .env file in the repo root or here."""

    model_config = SettingsConfigDict(env_file=("../../.env", ".env"), extra="ignore")

    database_url: str = "postgresql+psycopg://wearai:wearai@localhost:5432/wearai"
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
