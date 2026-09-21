"""Strategy A — deterministic compression (docs/architecture/ai-ml.md §2). No LLM call.

Safety rules (semantic correctness outranks token reduction):
- Fenced code blocks are never modified.
- Only *exact* duplicates (after case/punctuation/whitespace normalization) are removed,
  and only when they are at least MIN_DEDUPE_WORDS long, so short replies like "Yes." or
  "Do not." are never dropped. The first occurrence always survives.
- Output is never longer than the input.

Levels by mode:
- conservative: whitespace cleanup + duplicate line removal
- balanced / code / context: + duplicate sentence removal
- aggressive: + pleasantry/boilerplate removal
"""

from __future__ import annotations

import re

from optimization_core.entities import OptimizationChange
from optimization_core.enums import ChangeImpact, ChangeType, OptimizationMode, PromptType

MIN_DEDUPE_WORDS = 3

_FENCE_RE = re.compile(r"(```.*?```)", re.DOTALL)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_INLINE_SPACES_RE = re.compile(r"(?<=\S)[ \t]{2,}")
_BLANK_RUNS_RE = re.compile(r"\n{3,}")
_NON_WORD_EDGES_RE = re.compile(r"^\W+|\W+$")

_BOILERPLATE_RES = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bthanks? in advance\b[.!]?",
        r"\bthank you in advance\b[.!]?",
        r"\bi hope this (message|email) finds you well\b[.!,]?",
        r"\bthanks? for your (time|help)\b[.!]?",
    )
)


def _normalize(text: str) -> str:
    collapsed = " ".join(text.lower().split())
    return _NON_WORD_EDGES_RE.sub("", collapsed)


def _is_dedupable(normalized: str) -> bool:
    return len(normalized.split()) >= MIN_DEDUPE_WORDS


class DeterministicCompressionStrategy:
    name = "deterministic_compression"
    requires_llm_call = False

    def __init__(self, mode: OptimizationMode = OptimizationMode.BALANCED) -> None:
        self._mode = mode

    def applies_to(self, prompt_type: PromptType, mode: OptimizationMode) -> bool:
        return True

    def optimize(self, text: str) -> tuple[str, list[OptimizationChange]]:
        counts = {"whitespace": 0, "dedupe": 0, "boilerplate": 0}
        seen: set[str] = set()
        parts: list[str] = []

        for segment in _FENCE_RE.split(text):
            if segment.startswith("```") and segment.endswith("```") and len(segment) >= 6:
                parts.append(segment)
                continue
            prose = self._clean_whitespace(segment, counts)
            if self._mode is OptimizationMode.AGGRESSIVE:
                prose = self._strip_boilerplate(prose, counts)
            if self._mode is OptimizationMode.CONSERVATIVE:
                prose = self._dedupe_lines(prose, seen, counts)
            else:
                prose = self._dedupe_sentences(prose, seen, counts)
            parts.append(_BLANK_RUNS_RE.sub("\n\n", prose))

        optimized = "".join(parts).strip()
        if not optimized or len(optimized) >= len(text):
            return text, []
        return optimized, self._describe(counts)

    @staticmethod
    def _clean_whitespace(segment: str, counts: dict[str, int]) -> str:
        lines = []
        for line in segment.split("\n"):
            cleaned = _INLINE_SPACES_RE.sub(" ", line.rstrip())
            if cleaned != line:
                counts["whitespace"] += 1
            lines.append(cleaned)
        result = "\n".join(lines)
        collapsed = _BLANK_RUNS_RE.sub("\n\n", result)
        if collapsed != result:
            counts["whitespace"] += 1
        return collapsed

    @staticmethod
    def _strip_boilerplate(prose: str, counts: dict[str, int]) -> str:
        for pattern in _BOILERPLATE_RES:
            prose, n = pattern.subn("", prose)
            counts["boilerplate"] += n
        return prose

    @staticmethod
    def _dedupe_lines(prose: str, seen: set[str], counts: dict[str, int]) -> str:
        kept = []
        for line in prose.split("\n"):
            normalized = _normalize(line)
            if _is_dedupable(normalized):
                if normalized in seen:
                    counts["dedupe"] += 1
                    continue
                seen.add(normalized)
            kept.append(line)
        return "\n".join(kept)

    @staticmethod
    def _dedupe_sentences(prose: str, seen: set[str], counts: dict[str, int]) -> str:
        out_lines = []
        for line in prose.split("\n"):
            kept = []
            for sentence in _SENTENCE_SPLIT_RE.split(line):
                normalized = _normalize(sentence)
                if _is_dedupable(normalized):
                    if normalized in seen and sentence.strip():
                        counts["dedupe"] += 1
                        continue
                    seen.add(normalized)
                kept.append(sentence)
            out_lines.append(" ".join(kept))
        return "\n".join(out_lines)

    @staticmethod
    def _describe(counts: dict[str, int]) -> list[OptimizationChange]:
        changes: list[OptimizationChange] = []
        if counts["dedupe"]:
            changes.append(
                OptimizationChange(
                    type=ChangeType.DEDUPLICATION,
                    description=f"Removed {counts['dedupe']} exact duplicate line(s)/sentence(s)",
                    impact=ChangeImpact.LOW,
                )
            )
        if counts["boilerplate"]:
            changes.append(
                OptimizationChange(
                    type=ChangeType.BOILERPLATE_REMOVAL,
                    description=f"Removed {counts['boilerplate']} pleasantry phrase(s)",
                    impact=ChangeImpact.LOW,
                )
            )
        if counts["whitespace"]:
            changes.append(
                OptimizationChange(
                    type=ChangeType.WHITESPACE_CLEANUP,
                    description="Normalized redundant whitespace",
                    impact=ChangeImpact.LOW,
                )
            )
        return changes
