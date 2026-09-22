"""Deterministic safety gate for LLM-produced rewrites.

The LLM is untrusted output: before a rewrite may replace the user's prompt it must
prove it kept everything that cannot be lost — numbers, identifiers, quoted literals,
fenced code, negations — that it is actually shorter, and that it is still plausibly
*about the same thing* (a `topic_drift` check). That last one matters specifically
against prompt injection (see tests/test_prompt_injection.py): a compromised or
tricked provider can return a short, injection-obeying reply ("PWNED", a refusal, a
request for secrets) that has no numbers/identifiers/quotes/negations to lose and would
otherwise sail through. Requiring a minimum overlap of stemmed content words closes
that gap without needing to understand either text.

This is the minimum bar for *accepting* a rewrite; the semantic validator
(validator.py) then scores whatever was accepted. Failing this gate means "keep the
original".
"""

from __future__ import annotations

from optimization_core.features import extract

# Below this fraction of the original's content words surviving in the candidate, the
# rewrite is treated as off-topic rather than a compression of the same text. Only
# applied when the original has enough content words for the ratio to be meaningful.
_MIN_TOPIC_OVERLAP = 0.3
_MIN_ORIGINAL_CONTENT_WORDS = 3


def missing_critical_content(original: str, candidate: str) -> list[str]:
    """Names of the categories the candidate dropped; empty means it is safe."""
    o, c = extract(original), extract(candidate)
    problems: list[str] = []
    if any(block not in candidate for block in o.fenced_blocks):
        problems.append("fenced_code")
    if not o.numbers <= c.numbers:
        problems.append("numbers")
    if any(item not in c.prose for item in o.identifiers):
        problems.append("identifiers")
    if any(item not in c.prose for item in o.quoted_literals):
        problems.append("quoted_literals")
    if not o.negations <= c.negations:
        problems.append("negations")
    if len(candidate) >= len(original):
        problems.append("not_shorter")
    if len(o.content_words) >= _MIN_ORIGINAL_CONTENT_WORDS:
        overlap = len(o.content_words & c.content_words) / len(o.content_words)
        if overlap < _MIN_TOPIC_OVERLAP:
            problems.append("topic_drift")
    return problems
