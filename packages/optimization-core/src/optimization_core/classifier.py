"""Rule-based content classifier (IContentAnalyzer). Deliberately simple and
deterministic: it only needs to tell code-heavy prompts (which must not go to the LLM
compressor by default) from everything else."""

from __future__ import annotations

import re

from optimization_core.enums import PromptType

_CODE_LINE_RE = re.compile(
    # CodeQL (py/polynomial-redos): the original last two alternatives used `.*`
    # immediately followed by `\s*` — since `.` also matches whitespace, those two
    # quantified spans overlap, and for a long, unterminated line (e.g. many spaces
    # with no closing `)`/`{`/`}`/`;`) the engine explores exponentially many ways to
    # split the run between them before concluding failure. `classify()` runs this
    # against every line of an up-to-100,000-char, fully attacker-controlled prompt —
    # a real DoS vector, not just a lint nitpick. Fixed by replacing both `.*` with
    # negated character classes (`[^()]*`, `[^{};]*`): matching "anything except the
    # character I'm about to require next" has exactly one interpretation per
    # position, so there's nothing left to backtrack over — worst case is linear.
    r"^\s*(?:def |class |import |from \S+ import |function |const |let |var |return\b|"
    r"public |private |#include|SELECT |INSERT |UPDATE |DELETE |"
    r"[\w.]+\([^()]*\)\s*[{;:]?\s*$|[^{};]*[{};]\s*$)"
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
