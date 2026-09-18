"""Environment-driven configuration (§31: never hard-code secrets/config)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="AITO_", extra="ignore")

    environment: str = "development"

    # Tightened to specific extension/dashboard origins before production.
    cors_allow_origins: list[str] = ["*"]

    # Auth is wired but off by default in dev; enterprise deployments turn it on.
    require_api_key: bool = False
    api_key: str | None = None

    # Below this, an optimization result is marked requires_review and never auto-applied
    # (see docs/architecture/ai-ml.md §6 — enforced once the real validator lands in Phase 9).
    semantic_confidence_threshold: float = 0.85

    # Cost-optimization rule (docs/architecture/ai-ml.md §5): skip the LLM call when its
    # estimated cost would exceed the estimated token savings it could produce.
    cost_optimization_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
