from aito_tokenizers import HeuristicTokenizer
from optimization_core import HeuristicSemanticValidator, ModelRouter, RouterPolicy
from optimization_core.entities import OptimizationRequest, OptimizationResult
from optimization_core.enums import (
    ChangeType,
    OptimizationMode,
    PrivacyPolicy,
    TokenizerProvider,
)
from optimization_core.errors import ProviderError
from optimization_core.strategies import SemanticCompressionStrategy

from app.application.optimize_use_case import run_optimization
from app.application.tokenize_use_case import count_tokens, estimate_input_cost_usd

TOKENIZER = HeuristicTokenizer(TokenizerProvider.GENERIC)
NO_LLM = ModelRouter(None)


class FakeProvider:
    provider_id = "fake"

    def __init__(self, reply: str = "", error: Exception | None = None) -> None:
        self.reply, self.error, self.calls = reply, error, 0

    async def complete(self, *, system: str, user: str, max_tokens: int) -> str:
        self.calls += 1
        if self.error:
            raise self.error
        return self.reply


def llm_router(provider: FakeProvider, **policy: object) -> ModelRouter:
    return ModelRouter(
        SemanticCompressionStrategy(provider),
        RouterPolicy(llm_enabled=True, cost_optimization_enabled=False, **policy),  # type: ignore[arg-type]
    )


def make_request(
    text: str,
    mode: OptimizationMode = OptimizationMode.BALANCED,
    privacy: PrivacyPolicy = PrivacyPolicy.CLOUD_ALLOWED,
) -> OptimizationRequest:
    return OptimizationRequest(text=text, platform="chatgpt", mode=mode, privacy_policy=privacy)


async def run(
    request: OptimizationRequest,
    router: ModelRouter = NO_LLM,
    threshold: float = 0.85,
    price: float = 1.0,
) -> OptimizationResult:
    return await run_optimization(
        request,
        tokenizer=TOKENIZER,
        router=router,
        validator=HeuristicSemanticValidator(),
        confidence_threshold=threshold,
        input_price_per_1k_usd=price,
    )


LONG = (
    "Could you please write a Python function called parse_config that reads a YAML file "
    "and must not use eval? It should return at most 10 keys."
)
SAFE_REWRITE = "Write Python parse_config: read YAML, must not use eval, return at most 10 keys."


async def test_minimal_prompt_is_returned_unchanged() -> None:
    request = make_request("Please review this code for bugs.")

    result = await run(request)

    assert result.optimized_text == request.text
    assert result.tokens_saved == 0
    assert result.estimated_cost_saved == 0.0
    assert result.changes == ()
    assert result.requires_review is False


async def test_redundant_prompt_is_compressed_and_reports_changes() -> None:
    request = make_request(
        "Use PostgreSQL for the database.   Write unit tests.\n\n\n\n\n"
        "Use PostgreSQL for the database."
    )

    result = await run(request)

    assert result.optimized_text == "Use PostgreSQL for the database. Write unit tests."
    assert result.original_tokens == count_tokens(request.text, TOKENIZER)
    assert result.optimized_tokens == count_tokens(result.optimized_text, TOKENIZER)
    assert {c.type for c in result.changes} == {
        ChangeType.DEDUPLICATION,
        ChangeType.WHITESPACE_CLEANUP,
    }


async def test_structural_step_runs_in_balanced_but_not_conservative() -> None:
    text = "Could you please review this function?"
    balanced = await run(make_request(text))
    conservative = await run(make_request(text, OptimizationMode.CONSERVATIVE))

    assert balanced.optimized_text == "Review this function."
    assert [c.type for c in balanced.changes] == [ChangeType.STRUCTURAL_REWRITE]
    assert conservative.optimized_text == text


async def test_llm_result_is_used_when_router_selects_it() -> None:
    provider = FakeProvider(SAFE_REWRITE)

    result = await run(make_request(LONG), llm_router(provider))

    assert provider.calls == 1
    assert result.optimized_text == SAFE_REWRITE
    assert ChangeType.SEMANTIC_COMPRESSION in {c.type for c in result.changes}


async def test_llm_is_never_called_for_local_only_privacy() -> None:
    provider = FakeProvider(SAFE_REWRITE)

    result = await run(make_request(LONG, privacy=PrivacyPolicy.LOCAL_ONLY), llm_router(provider))

    assert provider.calls == 0
    assert ChangeType.SEMANTIC_COMPRESSION not in {c.type for c in result.changes}


async def test_llm_is_never_called_for_code_prompts() -> None:
    provider = FakeProvider("x")
    text = "Fix the bug in this snippet please.\n```py\nx = 1\n```"

    await run(make_request(text), llm_router(provider))

    assert provider.calls == 0


async def test_provider_failure_falls_back_to_deterministic_result() -> None:
    provider = FakeProvider(error=ProviderError("HTTP 500"))

    result = await run(make_request(LONG), llm_router(provider))

    assert provider.calls == 1
    assert result.optimized_text.startswith("Write a Python function")  # structural applied
    assert ChangeType.SEMANTIC_COMPRESSION not in {c.type for c in result.changes}


async def test_unsafe_llm_rewrite_is_discarded() -> None:
    provider = FakeProvider("Write a function that reads YAML.")  # drops parse_config, 10, "not"

    result = await run(make_request(LONG), llm_router(provider))

    assert "parse_config" in result.optimized_text
    assert ChangeType.SEMANTIC_COMPRESSION not in {c.type for c in result.changes}


async def test_estimated_cost_saved_uses_configured_price() -> None:
    request = make_request("Repeat this exact sentence twice. Repeat this exact sentence twice.")

    result = await run(request, price=2.0)

    assert result.estimated_cost_saved == result.tokens_saved / 1000 * 2.0
    assert result.estimated_cost_saved > 0


async def test_harmless_compression_is_not_flagged_for_review() -> None:
    request = make_request("Could you please review this function? Use PostgreSQL. Use PostgreSQL.")

    result = await run(request)

    assert result.optimized_text != request.text
    assert result.confidence >= 0.85 and result.requires_review is False
    assert result.validation.issues == ()


async def test_threshold_controls_requires_review() -> None:
    request = make_request("Repeat this exact sentence twice. Repeat this exact sentence twice.")

    assert (await run(request, threshold=1.1)).requires_review is True
    assert (await run(request, threshold=0.5)).requires_review is False


async def test_lossy_llm_rewrite_that_passes_the_gate_is_still_scored() -> None:
    # Keeps numbers/identifiers/negations (so the gate accepts it) but drops the format
    # requirement and named entity; the validator must reflect that loss.
    text = (
        "Please return the result as JSON and mention the PostgreSQL version in a friendly, "
        "detailed and thorough way, and do not include more than 5 rows."
    )
    provider = FakeProvider("Return result, mention version, do not include more than 5 rows.")

    result = await run(make_request(text), llm_router(provider))

    assert ChangeType.SEMANTIC_COMPRESSION in {c.type for c in result.changes}
    assert "missing_format_terms" in result.validation.issues
    assert result.confidence < 0.85 and result.requires_review is True


def test_estimate_input_cost() -> None:
    assert estimate_input_cost_usd(2000, 0.003) == 0.006
    assert estimate_input_cost_usd(0, 0.003) == 0.0
