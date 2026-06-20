from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Loaded from .env file
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ALGORITHM: str = "HS256"

    # API Keys loaded from environment variables / .env as fallbacks
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY:   Optional[str] = None

    # Ollama / Gemma (self-hosted or remote Ollama-compatible endpoint)
    OLLAMA_HOST:    str           = "http://164.52.211.238/api/generate"
    OLLAMA_MODEL:   str           = "gemma3:12b-it-q8_0"
    OLLAMA_API_KEY: Optional[str] = None    # leave blank if endpoint needs no auth

    # ── Business rule constants ─────────────────────────────────────────────
    # All numeric thresholds live here — never hardcode them in logic files.

    MAX_UTILISATION_PERCENT: int = 100
    # Max total allocation % any employee can have at one time.

    MIN_PASSWORD_LENGTH: int = 8
    # Minimum characters required for any password.

    DEFAULT_MAX_WEEKLY_HOURS: int = 40
    # Default cap on total hours an employee can log per week.
    # Can be changed by Admin in System Configuration screen.

    DEFAULT_SCHEDULER_INTERVAL_HOURS: int = 4
    # How often the background scheduler runs (hours).

    ATTENTION_DAYS_BEFORE_DEADLINE: int = 30
    # Project is flagged ATTENTION when end_date is this many days away.

    LOW_EFFORT_THRESHOLD_PERCENT: int = 50
    # If an employee logs less than this % of expected hours → AT_RISK flag.

    class Config:
        env_file = ".env"


settings = Settings()
