import pytest
from optimization_core.enums import TokenizerProvider
from optimization_core.interfaces import ITokenizer

from aito_tokenizers import HeuristicTokenizer, OpenAITokenizer, TokenizerRegistry


def test_heuristic_empty_is_zero_and_nonempty_is_positive() -> None:
    t = HeuristicTokenizer(TokenizerProvider.GENERIC)
    assert t.count_tokens("") == 0
    assert t.count_tokens("a") == 1


def test_heuristic_counts_punctuation_so_code_is_not_undercounted() -> None:
    t = HeuristicTokenizer(TokenizerProvider.GENERIC)
    assert t.count_tokens("f(x){return x;}") > len("f(x){return x;}") // 4


def test_heuristic_is_monotonic_in_text_length() -> None:
    t = HeuristicTokenizer(TokenizerProvider.GENERIC)
    assert t.count_tokens("hello world " * 10) > t.count_tokens("hello world")


def test_heuristic_rejects_bad_ratio() -> None:
    with pytest.raises(ValueError):
        HeuristicTokenizer(TokenizerProvider.GENERIC, chars_per_token=0)


def test_openai_tokenizer_counts_and_handles_special_token_text() -> None:
    t = OpenAITokenizer()
    assert t.count_tokens("") == 0
    assert t.count_tokens("Please review this code for bugs.") > 0
    assert t.count_tokens("<|endoftext|> literal") > 0
    if t.is_exact_bpe:
        assert t.count_tokens("Please review this code for bugs.") == 7


def test_openai_tokenizer_falls_back_when_encoding_unavailable() -> None:
    t = OpenAITokenizer(encoding_name="does-not-exist")
    assert t.is_exact_bpe is False
    assert t.count_tokens("Please review this code.") > 0


def test_registry_returns_provider_tokenizer_and_all_satisfy_protocol() -> None:
    registry = TokenizerRegistry()
    for provider in TokenizerProvider:
        tokenizer = registry.get(provider)
        assert isinstance(tokenizer, ITokenizer)
        assert tokenizer.provider == provider


def test_registry_requires_generic_fallback() -> None:
    with pytest.raises(ValueError):
        TokenizerRegistry({TokenizerProvider.OPENAI: HeuristicTokenizer(TokenizerProvider.OPENAI)})


def test_registry_falls_back_to_generic_for_unregistered_provider() -> None:
    generic = HeuristicTokenizer(TokenizerProvider.GENERIC)
    registry = TokenizerRegistry({TokenizerProvider.GENERIC: generic})
    assert registry.get(TokenizerProvider.ANTHROPIC) is generic
