"""Offline heuristic tokenizer. Counts word and punctuation chunks rather than a flat
chars/4, so symbol-heavy text (code, JSON) is not under-counted. This is an ESTIMATE:
providers do not publish exact offline tokenizers for every model, and the API always
labels results `estimated` (never `provider_reported`)."""

from __future__ import annotations

import math
import re

from optimization_core.enums import TokenizerProvider

_CHUNK_RE = re.compile(r"\w+|[^\w\s]")


class HeuristicTokenizer:
    def __init__(self, provider: TokenizerProvider, chars_per_token: float = 4.0) -> None:
        if chars_per_token <= 0:
            raise ValueError("chars_per_token must be positive")
        self.provider = provider
        self._chars_per_token = chars_per_token

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        total = sum(
            max(1, math.ceil(len(chunk) / self._chars_per_token))
            for chunk in _CHUNK_RE.findall(text)
        )
        return max(1, total)
