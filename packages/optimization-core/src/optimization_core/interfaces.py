"""Domain interfaces (structural typing via `Protocol`).

Every concrete implementation lives outside this package (in `packages/tokenizers`,
`packages/provider-adapters`, or `services/optimization-service/app/infrastructure`)
and is wired in at the composition root via dependency injection. Nothing in this
module imports a concrete implementation — that is the point: swapping a tokenizer,
provider, or strategy must never require touching call sites.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from optimization_core.entities import (
    OptimizationChange,
    OptimizationRequest,
    OptimizationResult,
    SemanticValidationResult,
)
from optimization_core.enums import OptimizationMode, PromptType, TokenizerProvider


@runtime_checkable
class ITokenizer(Protocol):
    """One implementation per provider: OpenAITokenizer, AnthropicTokenizer, etc."""

    provider: TokenizerProvider

    def count_tokens(self, text: str) -> int: ...


@runtime_checkable
class IContentAnalyzer(Protocol):
    """Classifies raw input so the pipeline can pick applicable strategies."""

    def classify(self, text: str) -> PromptType: ...


@runtime_checkable
class IRedundancyDetector(Protocol):
    """Deterministic redundancy/duplication detection (Strategy A/C) — no LLM call."""

    def find_redundancies(self, text: str) -> list[OptimizationChange]: ...

    def apply(self, text: str, changes: list[OptimizationChange]) -> str: ...


@runtime_checkable
class IOptimizationStrategy(Protocol):
    """One implementation per strategy A-F described in docs/architecture/ai-ml.md."""

    name: str
    requires_llm_call: bool

    def applies_to(self, prompt_type: PromptType, mode: OptimizationMode) -> bool: ...

    def optimize(self, text: str) -> tuple[str, list[OptimizationChange]]: ...


@runtime_checkable
class ISemanticValidator(Protocol):
    def validate(self, original_text: str, optimized_text: str) -> SemanticValidationResult: ...


@runtime_checkable
class IAIProvider(Protocol):
    """One implementation per provider: OpenAIProvider, AnthropicProvider, etc."""

    provider_id: str

    async def complete(self, prompt: str, *, max_tokens: int) -> str: ...


@runtime_checkable
class IModelRouter(Protocol):
    """Selects the strategy/provider to use for a request, enforcing privacy policy
    and the cost-optimization rule (estimated_cost >= estimated_savings -> skip LLM)."""

    def select(self, request: OptimizationRequest, prompt_type: PromptType) -> IOptimizationStrategy: ...


@runtime_checkable
class IOptimizationPipeline(Protocol):
    """Orchestrates: classify -> estimate -> deduplicate -> optimize -> validate."""

    async def run(self, request: OptimizationRequest) -> OptimizationResult: ...
