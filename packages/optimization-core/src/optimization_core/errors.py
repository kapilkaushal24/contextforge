class ProviderError(Exception):
    """Any failure talking to an AI provider (network, auth, rate limit, bad response).

    Messages must never include prompt text or credentials. Callers treat this as
    "LLM optimization unavailable" and fall back to the deterministic result."""
