"""Domain entities — plain dataclasses, no Pydantic/framework dependency.

The API layer (services/optimization-service/app/api) maps these to/from Pydantic DTOs
at the boundary; the domain layer itself never imports a web framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from optimization_core.enums import ChangeImpact, ChangeType, OptimizationMode, Platform, PrivacyPolicy


@dataclass(frozen=True, slots=True)
class OptimizationRequest:
    text: str
    platform: Platform
    mode: OptimizationMode
    privacy_policy: PrivacyPolicy
    conversation_context: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("text must not be empty")
        if len(self.text) > 100_000:
            raise ValueError("text exceeds max length of 100_000 characters")


@dataclass(frozen=True, slots=True)
class OptimizationChange:
    type: ChangeType
    description: str
    impact: ChangeImpact


@dataclass(frozen=True, slots=True)
class SemanticValidationResult:
    semantic_similarity: float
    constraint_preservation: float
    confidence: float

    def __post_init__(self) -> None:
        for name, value in (
            ("semantic_similarity", self.semantic_similarity),
            ("constraint_preservation", self.constraint_preservation),
            ("confidence", self.confidence),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1], got {value}")


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    original_text: str
    optimized_text: str
    original_tokens: int
    optimized_tokens: int
    optimization_mode: OptimizationMode
    validation: SemanticValidationResult
    requires_review: bool
    changes: tuple[OptimizationChange, ...] = field(default_factory=tuple)
    estimated_cost_saved: float = 0.0

    @property
    def tokens_saved(self) -> int:
        return self.original_tokens - self.optimized_tokens

    @property
    def reduction_percentage(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return (self.tokens_saved / self.original_tokens) * 100

    @property
    def confidence(self) -> float:
        return self.validation.confidence
