"""Local, deterministic sensitive-content detection (docs/security/privacy-security.md
§1: "PII/sensitive-data detection runs before any cloud LLM call; matches can block
cloud routing per policy"). No model, no network — this must run on every request at
near-zero cost, and it must never itself be a place prompt text leaves the process.

Scope and known limitations (documented rather than silently assumed):
- Deliberately precision-biased over recall for phone numbers and generic secrets —
  a bare, unseparated 10-digit run is common in non-phone contexts (order numbers,
  IDs), so phone detection requires a separator or a leading "+". This means some real
  phone numbers written without punctuation are missed; that tradeoff favors fewer
  false positives blocking legitimate cloud optimization.
- Credit card detection requires a Luhn-valid checksum, not just "looks like 16 digits".
- SSN pattern is US-specific (###-##-####).
- API-key detection is prefix-based for a handful of well-known providers (OpenAI,
  GitHub, Slack, AWS, Google) — an unrecognized secret format will not be caught here.
- Scans the full text, including fenced code, since pasted credentials in code are
  exactly the case that matters most.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE_RE = re.compile(
    r"(?<!\w)(?:"
    r"\(\d{2,4}\)[\s.-]?\d{3,4}[\s.-]?\d{3,4}"  # (415) 555-0132
    r"|\+\d{1,3}[\s.-]\d{2,4}[\s.-]\d{3,4}[\s.-]\d{3,4}"  # +1 415-555-0132
    r"|\d{2,4}[\s.-]\d{3,4}[\s.-]\d{3,4}"  # 415-555-0132 / 415.555.0132
    r")(?!\w)"
)
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
# A single bounded character-class repetition, not `(?:\d[ -]?){13,19}` (a group with
# an *optional* element repeated a bounded-but-large number of times). That shape is a
# textbook ReDoS pattern flagged by CodeQL's py/polynomial-redos: at every position the
# engine must explore separator-or-not across up to 19 repetitions, and this runs via
# `finditer` over the full request text (up to 100,000 untrusted chars, see
# OptimizationRequest's length limit) — i.e. exactly the attacker-controlled, long-input
# scenario that turns "slow" into a real denial-of-service. A character class like
# `[\d \-]` has no such ambiguity: each character is matched by one deterministic branch,
# so this is worst-case linear regardless of input, and the actual digit-count/Luhn check
# still happens in Python afterward (_has_credit_card) exactly as before.
_CARD_CANDIDATE_RE = re.compile(r"\b\d[\d \-]{11,30}\d\b")
_API_KEY_RE = re.compile(
    r"\b(?:sk|pk)-[A-Za-z0-9]{20,}\b"  # OpenAI/Stripe-style
    r"|\bgh[pous]_[A-Za-z0-9]{20,}\b"  # GitHub tokens
    r"|\bxox[baprs]-[A-Za-z0-9-]{10,}\b"  # Slack tokens
    r"|\bAKIA[0-9A-Z]{16}\b"  # AWS access key
    r"|\bAIza[0-9A-Za-z_-]{35}\b"  # Google API key
)

CATEGORIES = ("email", "phone", "ssn", "credit_card", "api_key")


@dataclass(frozen=True, slots=True)
class PiiMatch:
    category: str
    """One of CATEGORIES. Never carries the matched text itself — callers must not
    put this in a log line; only the category name is safe to log."""


def _luhn_valid(digits: str) -> bool:
    total = 0
    for index, ch in enumerate(reversed(digits)):
        value = int(ch)
        if index % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def _has_credit_card(text: str) -> bool:
    for candidate in _CARD_CANDIDATE_RE.finditer(text):
        digits = re.sub(r"[ -]", "", candidate.group())
        if 13 <= len(digits) <= 19 and _luhn_valid(digits):
            return True
    return False


def detect_pii(text: str) -> list[PiiMatch]:
    """Returns the distinct categories found, in a stable order. Empty means none of
    the known patterns matched — not a guarantee the text has no sensitive content."""
    found: list[PiiMatch] = []
    if _EMAIL_RE.search(text):
        found.append(PiiMatch("email"))
    if _PHONE_RE.search(text):
        found.append(PiiMatch("phone"))
    if _SSN_RE.search(text):
        found.append(PiiMatch("ssn"))
    if _has_credit_card(text):
        found.append(PiiMatch("credit_card"))
    if _API_KEY_RE.search(text):
        found.append(PiiMatch("api_key"))
    return found
