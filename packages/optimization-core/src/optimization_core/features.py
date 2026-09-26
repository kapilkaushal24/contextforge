"""Feature extraction shared by the LLM safety gate (safety.py) and the semantic
validator (validator.py), so "what must survive an optimization" is defined once.

Everything here is deterministic and local (no model, no network). Fenced code is kept
whole and excluded from prose analysis.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from optimization_core.fences import FENCE_RE, is_fenced_block

_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)*")
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
_IDENTIFIER_RE = re.compile(r"\b(?:[A-Za-z_]\w*[_.]\w[\w.]*|[a-z]+[A-Z]\w*)\b")
_QUOTED_RE = re.compile(r'"([^"\n]{2,})"|“([^”\n]{2,})”')
_NEGATION_RE = re.compile(
    r"\b(?:not|never|no|without|cannot|can't|don't|doesn't|won't|avoid|only|must not)\b",
    re.IGNORECASE,
)
_CONSTRAINT_RE = re.compile(
    r"\b(?:must|should|shall|always|exactly|at least|at most|no more than|no less than|"
    r"up to|maximum|minimum|required|mandatory|except|unless|edge cases?|corner cases?)\b",
    re.IGNORECASE,
)
_FORMAT_RE = re.compile(
    r"\b(?:json|yaml|xml|csv|markdown|table|bullets?|list|html|sql|step-by-step)\b", re.IGNORECASE
)
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")
_ACRONYM_RE = re.compile(r"^[A-Z]{2,}$")
_CAMEL_RE = re.compile(r"^[A-Z][a-z]+[A-Z]\w*$")

# Politeness, request wrappers and function words carry no task content. Modal/negation
# words are handled by the constraint/negation features, not as content words.
STOPWORDS = frozenset(
    [
        "a",
        "an",
        "and",
        "or",
        "but",
        "of",
        "to",
        "in",
        "on",
        "for",
        "with",
        "this",
        "that",
        "these",
        "those",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "it",
        "its",
        "as",
        "at",
        "by",
        "from",
        "if",
        "then",
        "so",
        "do",
        "does",
        "did",
        "have",
        "has",
        "had",
        "please",
        "kindly",
        "could",
        "would",
        "can",
        "will",
        "you",
        "your",
        "i",
        "me",
        "my",
        "we",
        "us",
        "our",
        "thanks",
        "thank",
        "hi",
        "hello",
        "also",
        "just",
        "really",
        "very",
        "want",
        "need",
        "like",
        "must",
        "should",
        "shall",
        "not",
        "never",
        "no",
        "only",
        "the",
        "there",
        "here",
        "which",
        "who",
        "what",
        "when",
        "how",
        "about",
        "into",
        "than",
        "some",
        "any",
        "all",
        "each",
        "more",
        "most",
        "such",
        "up",
        "out",
    ]
)
_SUFFIXES = ("ing", "edly", "ed", "es", "s", "ly")


def stem(word: str) -> str:
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


@dataclass(frozen=True, slots=True)
class Features:
    raw: str
    prose: str
    fenced_blocks: frozenset[str]
    numbers: frozenset[str]
    identifiers: frozenset[str]
    quoted_literals: frozenset[str]
    negations: frozenset[str]
    constraint_markers: frozenset[str]
    format_terms: frozenset[str]
    entities: frozenset[str]
    content_words: frozenset[str]


def _entities(prose: str) -> frozenset[str]:
    found: set[str] = set()
    for sentence in _SENTENCE_RE.split(prose):
        words = _WORD_RE.findall(sentence)
        for index, word in enumerate(words):
            if (
                _ACRONYM_RE.match(word)
                or _CAMEL_RE.match(word)
                or (index > 0 and word[0].isupper() and len(word) > 1)
            ):
                found.add(word)
    return frozenset(found)


def extract(text: str) -> Features:
    segments = FENCE_RE.split(text)
    prose = "".join(seg for seg in segments if not is_fenced_block(seg))
    quoted = {a or b for a, b in _QUOTED_RE.findall(prose)}
    words = {
        stem(w.lower())
        for w in _WORD_RE.findall(prose)
        if w.lower() not in STOPWORDS and len(w) > 1
    }
    return Features(
        raw=text,
        prose=prose,
        fenced_blocks=frozenset(seg for seg in segments if is_fenced_block(seg)),
        numbers=frozenset(_NUMBER_RE.findall(prose)),
        identifiers=frozenset(_INLINE_CODE_RE.findall(prose))
        | frozenset(_IDENTIFIER_RE.findall(prose)),
        quoted_literals=frozenset(quoted),
        negations=frozenset(m.lower() for m in _NEGATION_RE.findall(prose)),
        constraint_markers=frozenset(m.lower() for m in _CONSTRAINT_RE.findall(prose)),
        format_terms=frozenset(m.lower().rstrip("s") for m in _FORMAT_RE.findall(prose)),
        entities=_entities(prose),
        content_words=frozenset(words),
    )
