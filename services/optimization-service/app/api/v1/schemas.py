"""Pydantic v2 DTOs for the /api/v1 surface — the runtime-validated mirror of
packages/contracts/src/*.ts. Field names are declared snake_case (Python convention)
but serialize on the wire as camelCase via the alias generator, matching the TS
contracts exactly (e.g. `original_tokens` <-> `originalTokens`).

These are DTOs only: no business logic lives here (§36 coding rules), and routes never
return `optimization_core` domain objects directly (§42: no ORM/domain objects through
the public API — the same principle applies to any internal type).
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

Platform = str
"""Open, not a closed literal — mirrors packages/contracts Platform (ADR-009): the set
of known platforms is owned by the extension's registry, not hardcoded here."""

OptimizationMode = Literal["conservative", "balanced", "aggressive", "code", "context"]
PrivacyPolicy = Literal["cloud_allowed", "local_only"]
ChangeImpact = Literal["low", "medium", "high"]
TokenizerProvider = Literal["openai", "anthropic", "gemini", "generic"]


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# --- /optimize ---------------------------------------------------------------


class OptimizeRequest(CamelModel):
    text: str = Field(min_length=1, max_length=100_000)
    platform: Platform
    mode: OptimizationMode
    privacy_policy: PrivacyPolicy
    conversation_context: list[str] | None = None


class OptimizationChange(CamelModel):
    type: str
    description: str
    impact: ChangeImpact


class OptimizeResult(CamelModel):
    original_text: str
    optimized_text: str
    original_tokens: int
    optimized_tokens: int
    tokens_saved: int
    reduction_percentage: float
    estimated_cost_saved: float
    optimization_mode: OptimizationMode
    confidence: float
    requires_review: bool
    changes: list[OptimizationChange] = Field(default_factory=list)


# --- /analyze ------------------------------------------------------------------


class AnalyzeRequest(CamelModel):
    text: str = Field(min_length=1, max_length=100_000)


class AnalyzeResult(CamelModel):
    prompt_type: Literal["code", "documentation", "conversation", "general"]
    estimated_tokens: int
    has_detected_redundancy: bool


# --- /estimate-tokens ------------------------------------------------------------


class EstimateTokensRequest(CamelModel):
    text: str = Field(min_length=1, max_length=100_000)
    provider: TokenizerProvider = "generic"


class EstimateTokensResponse(CamelModel):
    tokens: int
    provider: TokenizerProvider
    method: Literal["estimated", "provider_reported"] = "estimated"


# --- /validate -------------------------------------------------------------------


class ValidateRequest(CamelModel):
    original_text: str = Field(min_length=1, max_length=100_000)
    optimized_text: str = Field(min_length=0, max_length=100_000)


class SemanticValidationResult(CamelModel):
    semantic_similarity: float = Field(ge=0.0, le=1.0)
    constraint_preservation: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)


# --- /providers, /models -----------------------------------------------------------


class ProviderInfo(CamelModel):
    id: str
    name: str
    status: Literal["available", "unavailable"]


class ModelInfo(CamelModel):
    id: str
    provider_id: str
    name: str
    input_price_per_1k: float
    output_price_per_1k: float


# --- /usage, /settings, /feedback -----------------------------------------------------


class UsageSummary(CamelModel):
    range_start: str
    range_end: str
    total_requests: int
    total_tokens_saved: int
    average_reduction_percentage: float
    estimated_cost_saved: float


class UserSettings(CamelModel):
    default_mode: OptimizationMode = "balanced"
    privacy_policy: PrivacyPolicy = "cloud_allowed"
    feature_flags: dict[str, bool] = Field(default_factory=dict)


class FeedbackRequest(CamelModel):
    request_id: str
    rating: Literal["helpful", "not_helpful"]
    reason: Literal["changed_intent", "too_aggressive", "other"] | None = None


class FeedbackAck(CamelModel):
    accepted: bool = True
