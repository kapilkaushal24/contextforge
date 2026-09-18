"""Placeholder content classification (Phase 5 skeleton): always "general", no
redundancy signal. Replaced by the real `IContentAnalyzer` / `IRedundancyDetector`
in Phase 6 (docs/architecture/ai-ml.md) — the route calling this does not change."""

from dataclasses import dataclass
from typing import Literal

from app.application.tokenize_use_case import estimate_tokens

PromptType = Literal["code", "documentation", "conversation", "general"]


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    prompt_type: PromptType
    estimated_tokens: int
    has_detected_redundancy: bool


def analyze(text: str) -> AnalysisResult:
    return AnalysisResult(prompt_type="general", estimated_tokens=estimate_tokens(text), has_detected_redundancy=False)
