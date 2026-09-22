"""Content analysis: rule-based code-vs-general classification (Phase 8). The redundancy
signal is still a placeholder (`False`) until a real `IRedundancyDetector` lands."""

from dataclasses import dataclass
from typing import Literal

from optimization_core.classifier import RuleBasedContentAnalyzer
from optimization_core.interfaces import ITokenizer

from app.application.tokenize_use_case import count_tokens

PromptType = Literal["code", "documentation", "conversation", "general"]
_analyzer = RuleBasedContentAnalyzer()


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    prompt_type: PromptType
    estimated_tokens: int
    has_detected_redundancy: bool


def analyze(text: str, tokenizer: ITokenizer) -> AnalysisResult:
    return AnalysisResult(
        prompt_type=_analyzer.classify(text).value,
        estimated_tokens=count_tokens(text, tokenizer),
        has_detected_redundancy=False,
    )
