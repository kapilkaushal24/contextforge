from __future__ import annotations

from collections.abc import Mapping

from optimization_core.enums import TokenizerProvider
from optimization_core.interfaces import ITokenizer

from aito_tokenizers.heuristic import HeuristicTokenizer
from aito_tokenizers.openai import OpenAITokenizer

# Claude/Gemini have no offline exact tokenizer here: heuristics with per-provider
# calibration. Swap an entry for a real implementation without touching callers.
_ANTHROPIC_CHARS_PER_TOKEN = 3.5
_GEMINI_CHARS_PER_TOKEN = 4.0


class TokenizerRegistry:
    def __init__(self, tokenizers: Mapping[TokenizerProvider, ITokenizer] | None = None) -> None:
        self._tokenizers: dict[TokenizerProvider, ITokenizer] = dict(
            tokenizers if tokenizers is not None else _default_tokenizers()
        )
        if TokenizerProvider.GENERIC not in self._tokenizers:
            raise ValueError("registry requires a GENERIC fallback tokenizer")

    def get(self, provider: TokenizerProvider) -> ITokenizer:
        return self._tokenizers.get(provider, self._tokenizers[TokenizerProvider.GENERIC])


def _default_tokenizers() -> dict[TokenizerProvider, ITokenizer]:
    return {
        TokenizerProvider.OPENAI: OpenAITokenizer(),
        TokenizerProvider.ANTHROPIC: HeuristicTokenizer(
            TokenizerProvider.ANTHROPIC, _ANTHROPIC_CHARS_PER_TOKEN
        ),
        TokenizerProvider.GEMINI: HeuristicTokenizer(
            TokenizerProvider.GEMINI, _GEMINI_CHARS_PER_TOKEN
        ),
        TokenizerProvider.GENERIC: HeuristicTokenizer(TokenizerProvider.GENERIC),
    }
