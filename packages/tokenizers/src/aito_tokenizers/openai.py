"""OpenAI tokenizer backed by tiktoken (optional dependency). Local BPE counting is
close to what the API bills but is still labeled an estimate by the API layer."""

from __future__ import annotations

from typing import Any

from optimization_core.enums import TokenizerProvider

from aito_tokenizers.heuristic import HeuristicTokenizer


class OpenAITokenizer:
    provider = TokenizerProvider.OPENAI

    def __init__(self, encoding_name: str = "o200k_base") -> None:
        self._encoding: Any | None = None
        self._fallback = HeuristicTokenizer(TokenizerProvider.OPENAI)
        try:
            import tiktoken

            self._encoding = tiktoken.get_encoding(encoding_name)
        except Exception:  # noqa: BLE001 - any load failure (import, unknown name, offline) -> heuristic
            self._encoding = None

    @property
    def is_exact_bpe(self) -> bool:
        return self._encoding is not None

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        if self._encoding is None:
            return self._fallback.count_tokens(text)
        return max(1, len(self._encoding.encode(text, disallowed_special=())))
