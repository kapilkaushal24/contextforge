"""Strategy B — structural optimization (rule-based, no LLM).

Only rewrites that provably keep meaning: removes an *explicit request wrapper* from the
start of a sentence ("Could you please review X?" -> "Review X."). Wrappers that are
merely capability questions ("Can you access the internet?") are NOT touched, because
dropping them would turn a question into a command. Sentences whose remainder starts with
a negation are left alone too ("could you please not use recursion" must stay intact).
Fenced code is never modified.
"""

from __future__ import annotations

import re

from optimization_core.entities import OptimizationChange
from optimization_core.enums import ChangeImpact, ChangeType, OptimizationMode, PromptType
from optimization_core.fences import FENCE_RE, is_fenced_block

_WRAPPER_RE = re.compile(
    r"^(?:(?:can|could|would|will) you (?:please|kindly) "
    r"|please (?:can|could|would) you "
    r"|i(?:'d| would) like you to "
    r"|i want you to "
    r"|i need you to )(?P<rest>.+)$",
    re.IGNORECASE | re.DOTALL,
)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])(\s+)")
_NEGATED_REST_RE = re.compile(r"^(?:not|never|no)\b|^\w+n't\b", re.IGNORECASE)


def _unwrap(sentence: str) -> str | None:
    stripped = sentence.strip()
    match = _WRAPPER_RE.match(stripped)
    if match is None:
        return None
    rest = match.group("rest").strip()
    if not rest or _NEGATED_REST_RE.match(rest):
        return None
    rest = rest[0].upper() + rest[1:]
    if rest.endswith("?"):
        rest = rest[:-1] + "."
    leading = sentence[: len(sentence) - len(sentence.lstrip())]
    return leading + rest


class StructuralOptimizationStrategy:
    name = "structural_optimization"
    requires_llm_call = False

    def applies_to(self, prompt_type: PromptType, mode: OptimizationMode) -> bool:
        return mode in (OptimizationMode.BALANCED, OptimizationMode.AGGRESSIVE)

    async def optimize(self, text: str) -> tuple[str, list[OptimizationChange]]:
        rewrites = 0
        parts: list[str] = []
        for segment in FENCE_RE.split(text):
            if is_fenced_block(segment):
                parts.append(segment)
                continue
            pieces = _SENTENCE_SPLIT_RE.split(segment)
            for i in range(0, len(pieces), 2):
                unwrapped = _unwrap(pieces[i])
                if unwrapped is not None:
                    pieces[i] = unwrapped
                    rewrites += 1
            parts.append("".join(pieces))

        optimized = "".join(parts)
        if not rewrites or len(optimized) >= len(text):
            return text, []
        return optimized, [
            OptimizationChange(
                type=ChangeType.STRUCTURAL_REWRITE,
                description=f"Removed {rewrites} request wrapper phrase(s) (e.g. 'could you please')",
                impact=ChangeImpact.LOW,
            )
        ]
