from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings read from environment variables, or from a .env file in the repo root or here."""

    model_config = SettingsConfigDict(env_file=("../../.env", ".env"), extra="ignore")

    database_url: str = "postgresql+psycopg://wearai:wearai@localhost:5432/wearai"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Order references look like WA-7K2M9QXP.
    order_reference_prefix: str = "WA"

    session_cookie_name: str = "session"
    session_days: int = 14
    # Set to true in production so the cookie is only sent over HTTPS.
    cookie_secure: bool = False


settings = Settings()
