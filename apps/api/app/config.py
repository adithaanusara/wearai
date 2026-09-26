from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings read from environment variables, or from a .env file in the repo root or here."""

    model_config = SettingsConfigDict(env_file=("../../.env", ".env"), extra="ignore")

    database_url: str = "postgresql+psycopg://wearai:wearai@localhost:5432/wearai"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Order references look like WA-7K2M9QXP.
    order_reference_prefix: str = "WA"

    # --- Chat assistant (Anthropic API). The key stays on the server and is never sent to browsers.
    anthropic_api_key: str | None = None
    store_name: str = "WEARAI"
    chat_enabled: bool = True
    chat_model: str = "claude-opus-5"
    # The next three suit Claude Opus 5 and Sonnet 5. For Haiku 4.5 set thinking, effort and
    # fallbacks off (CHAT_ADAPTIVE_THINKING=false, CHAT_EFFORT=none, CHAT_REFUSAL_FALLBACKS=false).
    chat_adaptive_thinking: bool = True
    chat_effort: Literal["low", "medium", "high", "none"] = "low"
    chat_refusal_fallbacks: bool = True
    # Thinking tokens count towards this, so leave room for the answer as well.
    chat_max_output_tokens: int = 2048
    chat_max_tool_rounds: int = 5
    chat_timeout_seconds: float = 30.0
    # What one visitor may send.
    chat_max_messages: int = 20
    chat_max_message_chars: int = 1000
    chat_max_total_chars: int = 6000
    # Cost and abuse limits, kept in the database so they hold across server processes.
    chat_rate_limit_requests: int = 20
    chat_rate_limit_window_seconds: int = 600
    chat_daily_token_cap: int = 2_000_000
    # Visitors are told apart by a salted hash of their address, so raw addresses are never stored.
    # Set this to a long random value in production.
    chat_hash_salt: str = "dev-only-change-me"

    session_cookie_name: str = "session"
    session_days: int = 14
    # Set to true in production so the cookie is only sent over HTTPS.
    cookie_secure: bool = False


settings = Settings()
