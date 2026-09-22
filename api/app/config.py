from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.

    Defaults are chosen so `uvicorn app.main:app` works with nothing else
    running — SQLite on disk, no Redis, no API key. Every external dependency
    degrades to a local equivalent rather than failing at import time.
    """

    model_config = SettingsConfigDict(env_prefix="SYNAPSE_", env_file=".env")

    database_url: str = "sqlite:///./synapse.db"
    redis_url: str | None = None

    # Claude. The SDK resolves ANTHROPIC_API_KEY itself; we only carry the
    # knobs. Leave the key unset and the specialist endpoints return 503
    # rather than pretending.
    # Read from the environment OR api/.env. Un-prefixed on purpose: it is the
    # name the SDK and every Anthropic doc uses. Never logged, never returned.
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")

    model: str = "claude-opus-5"
    effort: str = "high"
    max_tokens: int = 16000

    # Cost assumptions live in config, not in a prompt, because they are
    # commercial policy rather than model output.
    contractor_overhead_pct: float = 15.0
    contingency_pct: float = 5.0

    # Readiness weights — a starting guess, to be tuned against real projects.
    w_budget: float = 0.35
    w_compliance: float = 0.25
    w_buildability: float = 0.25
    w_sustainability: float = 0.15

    cors_origins: str = "*"

    # Where the two pages live, when the API serves them itself. Empty means
    # "../web next to the api directory", which is the repo layout.
    static_dir: str | None = None


@lru_cache
def settings() -> Settings:
    return Settings()
