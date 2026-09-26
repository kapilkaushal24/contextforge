"""Shared enums mirroring packages/contracts/src/enums.ts.

Kept as `StrEnum` (Python 3.11+) so values serialize identically to the TS
string-union side while also being real `str` instances.
"""

from enum import StrEnum


class OptimizationMode(StrEnum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    CODE = "code"
    CONTEXT = "context"


class PrivacyPolicy(StrEnum):
    CLOUD_ALLOWED = "cloud_allowed"
    LOCAL_ONLY = "local_only"


# Deliberately a plain `str` alias, not a closed Enum — the set of known platforms is
# defined by the extension's platform registry (apps/chrome-extension/src/constants/
# platforms.ts) and auto-detected from the active tab's URL, not hardcoded on the
# backend either (ADR-009). "generic" is reserved for any unrecognized platform.
Platform = str


class PromptType(StrEnum):
    CODE = "code"
    DOCUMENTATION = "documentation"
    CONVERSATION = "conversation"
    GENERAL = "general"


class TokenizerProvider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    GENERIC = "generic"


class ChangeImpact(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ChangeType(StrEnum):
    DEDUPLICATION = "deduplication"
    WHITESPACE_CLEANUP = "whitespace_cleanup"
    BOILERPLATE_REMOVAL = "boilerplate_removal"
    STRUCTURAL_REWRITE = "structural_rewrite"
    SEMANTIC_COMPRESSION = "semantic_compression"
    CONTEXT_DEDUPLICATION = "context_deduplication"
