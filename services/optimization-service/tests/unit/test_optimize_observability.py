"""Phase 12: per-stage timing logs and metrics emitted by run_optimization."""

import logging

import pytest
from aito_tokenizers import HeuristicTokenizer
from optimization_core import HeuristicSemanticValidator, ModelRouter, RouterPolicy
from optimization_core.entities import OptimizationRequest
from optimization_core.enums import OptimizationMode, PrivacyPolicy, TokenizerProvider
from optimization_core.strategies import SemanticCompressionStrategy

from app.application.optimize_use_case import run_optimization
from app.observability.metrics import (
    llm_requests_total,
    optimize_requests_total,
    semantic_validation_failures_total,
)

TOKENIZER = HeuristicTokenizer(TokenizerProvider.GENERIC)
NO_LLM = ModelRouter(None)


class FakeProvider:
    provider_id = "fake"

    def __init__(self, reply: str = "") -> None:
        self.reply = reply

    async def complete(self, *, system: str, user: str, max_tokens: int) -> str:
        return self.reply


def make_request(text: str) -> OptimizationRequest:
    return OptimizationRequest(
        text=text, platform="chatgpt", mode=OptimizationMode.BALANCED, privacy_policy=PrivacyPolicy.CLOUD_ALLOWED
    )


async def test_logs_per_stage_timings(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="app.application.optimize_use_case"):
        await run_optimization(
            make_request("Use PostgreSQL for the database. Use PostgreSQL for the database."),
            tokenizer=TOKENIZER,
            router=NO_LLM,
            validator=HeuristicSemanticValidator(),
            confidence_threshold=0.85,
            input_price_per_1k_usd=1.0,
        )

    timing_records = [r for r in caplog.records if r.message == "optimize pipeline stage timings"]
    assert len(timing_records) == 1
    record = timing_records[0]
    assert "deterministic" in record.stage_ms  # type: ignore[attr-defined]
    assert record.total_ms >= record.stage_ms["deterministic"]  # type: ignore[attr-defined]
    assert record.requires_review is False  # type: ignore[attr-defined]


async def test_optimize_requests_total_increments_with_mode_label() -> None:
    before = optimize_requests_total.labels(mode="balanced", outcome="success")._value.get()

    await run_optimization(
        make_request("Explain recursion simply, in your own words, to a beginner."),
        tokenizer=TOKENIZER,
        router=NO_LLM,
        validator=HeuristicSemanticValidator(),
        confidence_threshold=0.85,
        input_price_per_1k_usd=1.0,
    )

    after = optimize_requests_total.labels(mode="balanced", outcome="success")._value.get()
    assert after == before + 1


async def test_semantic_validation_failure_metric_increments_when_review_required() -> None:
    before = semantic_validation_failures_total._value.get()

    await run_optimization(
        make_request("Repeat this exact sentence twice. Repeat this exact sentence twice."),
        tokenizer=TOKENIZER,
        router=NO_LLM,
        validator=HeuristicSemanticValidator(),
        confidence_threshold=1.1,  # forces requires_review regardless of score
        input_price_per_1k_usd=1.0,
    )

    after = semantic_validation_failures_total._value.get()
    assert after == before + 1


async def test_llm_requests_total_increments_on_success() -> None:
    provider = FakeProvider("Write Python parse_config: read YAML.")
    router = ModelRouter(
        SemanticCompressionStrategy(provider),
        RouterPolicy(llm_enabled=True, cost_optimization_enabled=False),
    )
    before = llm_requests_total.labels(outcome="success")._value.get()

    await run_optimization(
        make_request(
            "Could you please write a Python function called parse_config that reads a YAML file?"
        ),
        tokenizer=TOKENIZER,
        router=router,
        validator=HeuristicSemanticValidator(),
        confidence_threshold=0.85,
        input_price_per_1k_usd=1.0,
    )

    after = llm_requests_total.labels(outcome="success")._value.get()
    assert after == before + 1
