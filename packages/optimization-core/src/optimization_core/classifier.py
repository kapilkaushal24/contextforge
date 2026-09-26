"""Rule-based content classifier (IContentAnalyzer). Deliberately simple and
deterministic: it only needs to tell code-heavy prompts (which must not go to the LLM
compressor by default) from everything else."""

from __future__ import annotations

import re

from optimization_core.enums import PromptType

_CODE_LINE_RE = re.compile(
    # CodeQL (py/polynomial-redos), two rounds: round 1 replaced `.*` adjacent to
    # `\s*` with negated character classes (`[^()]*`, `[^{};]*`), but that still left
    # a subtler overlap CodeQL kept flagging — `^\s*` immediately followed by
    # `[^{};]*` (whose negated class *also* matches whitespace), and `\s*[{;:]?\s*$`
    # (two `\s*` spans separated only by an optional non-whitespace class). For a
    # long run of spaces, both shapes let the engine explore many ways to split the
    # run between the two quantifiers before concluding failure — same polynomial-
    # backtracking class as round 1, just relocated. `classify()` runs this against
    # every line of an up-to-100,000-char, fully attacker-controlled prompt, so this
    # is a real DoS vector. Fixed for good with possessive quantifiers (`*+`, `++`;
    # Python 3.11+, and this project requires >=3.12): a possessive quantifier
    # commits to its match and never backtracks, which removes the ambiguity
    # structurally instead of just moving it — verified byte-for-byte identical
    # match results against the old pattern across every existing test input plus a
    # battery of adversarial/edge-case strings before landing this change.
    r"^\s*+(?:def |class |import |from \S++ import |function |const |let |var |return\b|"
    r"public |private |#include|SELECT |INSERT |UPDATE |DELETE |"
    r"[\w.]++\([^()]*+\)\s*+[{;:]?\s*+$|[^{};]*+[{};]\s*+$)"
)
_CODE_LINE_RATIO = 0.3


class RuleBasedContentAnalyzer:
    def classify(self, text: str) -> PromptType:
        if "```" in text:
            return PromptType.CODE
        lines = [line for line in text.splitlines() if line.strip()]
        if len(lines) >= 3:
            code_lines = sum(1 for line in lines if _CODE_LINE_RE.match(line))
            if code_lines / len(lines) >= _CODE_LINE_RATIO:
                return PromptType.CODE
        return PromptType.GENERAL
