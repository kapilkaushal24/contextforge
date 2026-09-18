"""Shared enums mirroring packages/contracts/src/enums.ts.

Kept as `str, Enum` so values serialize identically to the TS string-union side.
"""

from enum import Enum


class OptimizationMode(str, Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    CODE = "code"
    CONTEXT = "context"


class PrivacyPolicy(str, Enum):
    CLOUD_ALLOWED = "cloud_allowed"
    LOCAL_ONLY = "local_only"


class Platform(str, Enum):
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    GEMINI = "gemini"
    GENERIC = "generic"


class PromptType(str, Enum):
    CODE = "code"
    DOCUMENTATION = "documentation"
    CONVERSATION = "conversation"
    GENERAL = "general"


class TokenizerProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    GENERIC = "generic"


class ChangeImpact(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ChangeType(str, Enum):
    DEDUPLICATION = "deduplication"
    WHITESPACE_CLEANUP = "whitespace_cleanup"
    BOILERPLATE_REMOVAL = "boilerplate_removal"
    STRUCTURAL_REWRITE = "structural_rewrite"
    SEMANTIC_COMPRESSION = "semantic_compression"
    CONTEXT_DEDUPLICATION = "context_deduplication"
