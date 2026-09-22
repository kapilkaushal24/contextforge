"""Deterministic safety gate for LLM-produced rewrites.

The LLM is untrusted output: before a rewrite may replace the user's prompt it must
prove it kept everything that cannot be lost — numbers, identifiers, quoted literals,
fenced code, negations — and that it is actually shorter. This is the minimum bar for
*accepting* a rewrite; the semantic validator (validator.py) then scores whatever was
accepted. Failing this gate means "keep the original".
"""

from __future__ import annotations

from optimization_core.features import extract


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
    return problems
