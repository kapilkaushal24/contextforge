"""Rule-based content classifier (IContentAnalyzer). Deliberately simple and
deterministic: it only needs to tell code-heavy prompts (which must not go to the LLM
compressor by default) from everything else."""

from __future__ import annotations

import re

from optimization_core.enums import PromptType

_CODE_LINE_RE = re.compile(
    r"^\s*(?:def |class |import |from \S+ import |function |const |let |var |return\b|"
    r"public |private |#include|SELECT |INSERT |UPDATE |DELETE |"
    r"[\w.]+\(.*\)\s*[{;:]?\s*$|.*[{};]\s*$)"
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
