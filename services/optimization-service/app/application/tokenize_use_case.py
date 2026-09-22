"""Token counting and cost estimation. Counting is delegated to an injected
`ITokenizer` (implementations live in packages/tokenizers); results are ESTIMATES and
the API labels them so — never provider-billed actuals (docs/architecture/ai-ml.md §3).
"""

from optimization_core.interfaces import ITokenizer


def count_tokens(text: str, tokenizer: ITokenizer) -> int:
    return tokenizer.count_tokens(text)


def estimate_input_cost_usd(tokens: int, price_per_1k_usd: float) -> float:
    """Estimated input cost for `tokens` at a configured per-1k-token price."""
    return tokens / 1000 * price_per_1k_usd
