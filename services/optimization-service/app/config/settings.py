"""Environment-driven configuration (§31: never hard-code secrets/config)."""

from functools import lru_cache

from pydantic import SecretStr
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

    # Which tokenizer provider to use per platform id. Config, not code: platform ids are
    # open strings (ADR-009); unmapped platforms use the generic tokenizer.
    platform_tokenizer_map: dict[str, str] = {
        "chatgpt": "openai",
        "claude": "anthropic",
        "gemini": "gemini",
    }

    # Per-1k-input-token USD price used ONLY for estimated cost savings. Model prices
    # change; set this to your model's current price. Never presented as billed cost.
    input_price_per_1k_usd: float = 0.003

    # --- LLM (semantic) optimization: off unless explicitly enabled AND a key is set ---
    enable_llm_optimization: bool = False
    llm_provider: str = "openai"  # "openai" | "anthropic"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: SecretStr | None = None
    llm_timeout_seconds: float = 20.0
    # Prices of the optimizer LLM itself, used by the router's cost gate (USD per 1k tokens).
    llm_input_price_per_1k_usd: float = 0.00015
    llm_output_price_per_1k_usd: float = 0.0006

    # Phase 11 (docs/security/privacy-security.md §1): detected PII/secrets (email, phone,
    # SSN, credit card, API key) block cloud LLM routing regardless of privacy_policy. An
    # org that has accepted that risk can opt out explicitly.
    block_pii_from_cloud: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
