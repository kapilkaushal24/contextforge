"""Coarse placeholder token estimate (~4 chars/token, a commonly cited rule of thumb
for English text). Every caller goes through this one function so its Phase 7
replacement with real per-provider `ITokenizer` implementations
(docs/architecture/ai-ml.md §3) touches nothing else.
"""


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)
