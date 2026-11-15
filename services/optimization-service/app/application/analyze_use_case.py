"""Content analysis: rule-based classification and exact prose redundancy detection."""

import re
from dataclasses import dataclass
from typing import Literal

from optimization_core.classifier import RuleBasedContentAnalyzer
from optimization_core.fences import FENCE_RE, is_fenced_block
from optimization_core.interfaces import ITokenizer

from app.application.tokenize_use_case import count_tokens

PromptType = Literal["code", "documentation", "conversation", "general"]
_analyzer = RuleBasedContentAnalyzer()
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_NON_WORD_EDGES_RE = re.compile(r"^\W+|\W+$")
_MIN_REDUNDANCY_WORDS = 3


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    prompt_type: PromptType
    estimated_tokens: int
    has_detected_redundancy: bool


def analyze(text: str, tokenizer: ITokenizer) -> AnalysisResult:
    return AnalysisResult(
        prompt_type=_analyzer.classify(text).value,
        estimated_tokens=count_tokens(text, tokenizer),
        has_detected_redundancy=has_detected_redundancy(text),
    )


def has_detected_redundancy(text: str) -> bool:
    """Return true for repeated prose lines or sentences, matching optimizer rules.

    Fenced code is excluded because repeated code may be intentional. Short phrases are
    ignored to avoid flagging common replies or fragments such as "yes" or "do not".
    """
    seen: set[str] = set()
    for segment in FENCE_RE.split(text):
        if is_fenced_block(segment):
            continue
        for line in segment.splitlines():
            for sentence in _SENTENCE_SPLIT_RE.split(line):
                normalized = _NON_WORD_EDGES_RE.sub("", " ".join(sentence.casefold().split()))
                if len(normalized.split()) < _MIN_REDUNDANCY_WORDS:
                    continue
                if normalized in seen:
                    return True
                seen.add(normalized)
    return False
