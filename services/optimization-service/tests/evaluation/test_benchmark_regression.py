"""CI-friendly counterpart to ml/evaluation/run_eval.py: runs the same benchmark
dataset (single source of truth — ml/evaluation/datasets/benchmark_prompts.jsonl) but
in-process against `run_optimization` directly, with the LLM step disabled. That makes
it fast, deterministic, and runnable with no server, no network, and no API keys — a
regression gate for "did a change to the deterministic/structural pipeline or the
validator quietly make optimization worse or the safety checks looser," not a
replacement for ml/evaluation/run_eval.py's live, human-readable report.

Bounds below are set with real headroom below what a healthy pipeline currently
achieves (see a recent `python ml/evaluation/run_eval.py` run) — they exist to catch a
regression, not to enforce a specific score.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import pytest
from aito_tokenizers import HeuristicTokenizer
from optimization_core import HeuristicSemanticValidator, ModelRouter
from optimization_core.entities import OptimizationRequest
from optimization_core.enums import OptimizationMode, PrivacyPolicy, TokenizerProvider

from app.application.optimize_use_case import run_optimization

DATASET_PATH = (
    Path(__file__).resolve().parents[4] / "ml" / "evaluation" / "datasets" / "benchmark_prompts.jsonl"
)

TOKENIZER = HeuristicTokenizer(TokenizerProvider.GENERIC)
NO_LLM_ROUTER = ModelRouter(None)
VALIDATOR = HeuristicSemanticValidator()

MIN_AVG_REDUCTION_FOR_REDUCIBLE_PROMPTS = 15.0
MAX_LATENCY_MS_PER_PROMPT = 1000.0


def load_dataset() -> list[dict[str, Any]]:
    assert DATASET_PATH.exists(), f"benchmark dataset not found at {DATASET_PATH}"
    return [json.loads(line) for line in DATASET_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


DATASET = load_dataset()


@pytest.fixture(scope="module")
def results() -> list[dict[str, Any]]:
    """Runs the whole dataset once per test session and shares it across the
    assertions below — the pipeline call itself is what's expensive, not the checks."""
    collected = []
    for entry in DATASET:
        request = OptimizationRequest(
            text=entry["text"],
            platform="generic",
            mode=OptimizationMode(entry["mode"]),
            privacy_policy=PrivacyPolicy.CLOUD_ALLOWED,
        )
        started = time.perf_counter()
        result = asyncio.run(
            run_optimization(
                request,
                tokenizer=TOKENIZER,
                router=NO_LLM_ROUTER,
                validator=VALIDATOR,
                confidence_threshold=0.85,
                input_price_per_1k_usd=0.003,
            )
        )
        latency_ms = (time.perf_counter() - started) * 1000
        collected.append({"entry": entry, "result": result, "latency_ms": latency_ms})
    return collected


def test_dataset_is_not_empty() -> None:
    assert len(DATASET) >= 10
    assert {e["category"] for e in DATASET} >= {"coding", "sql", "documentation", "business"}


def test_no_prompt_errors_or_times_out(results: list[dict[str, Any]]) -> None:
    for item in results:
        assert item["latency_ms"] < MAX_LATENCY_MS_PER_PROMPT, (
            f"{item['entry']['id']} took {item['latency_ms']:.0f}ms (ceiling {MAX_LATENCY_MS_PER_PROMPT}ms)"
        )


def test_baseline_prompts_are_never_shrunk(results: list[dict[str, Any]]) -> None:
    """Prompts marked expect_reduction=false are already minimal — any reduction on
    them would mean the deterministic strategies are being too aggressive (a false
    positive), not that optimization improved."""
    baseline = [r for r in results if not r["entry"]["expect_reduction"]]
    assert baseline, "dataset should include at least one baseline (non-reducible) prompt"
    for item in baseline:
        assert item["result"].reduction_percentage == 0.0, (
            f"{item['entry']['id']} was expected to stay unchanged but shrank "
            f"by {item['result'].reduction_percentage:.1f}%"
        )


def test_reducible_prompts_achieve_meaningful_average_reduction(results: list[dict[str, Any]]) -> None:
    reducible = [r for r in results if r["entry"]["expect_reduction"]]
    assert reducible, "dataset should include at least one reducible prompt"
    avg = sum(r["result"].reduction_percentage for r in reducible) / len(reducible)
    assert avg >= MIN_AVG_REDUCTION_FOR_REDUCIBLE_PROMPTS, (
        f"average reduction across reducible prompts dropped to {avg:.1f}% "
        f"(floor {MIN_AVG_REDUCTION_FOR_REDUCIBLE_PROMPTS}%) — possible regression in "
        f"the deterministic/structural strategies"
    )


def test_every_reducible_prompt_shrinks_at_least_a_little(results: list[dict[str, Any]]) -> None:
    reducible = [r for r in results if r["entry"]["expect_reduction"]]
    zero_reduction = [r["entry"]["id"] for r in reducible if r["result"].reduction_percentage <= 0.0]
    assert zero_reduction == [], f"expected some reduction but got none for: {zero_reduction}"


def test_no_prompt_is_unexpectedly_flagged_for_review(results: list[dict[str, Any]]) -> None:
    """None of these prompts are adversarial (that's tests/security/'s job) — a clean
    prompt getting requires_review=True here signals a validator/safety-gate regression."""
    flagged = [item["entry"]["id"] for item in results if item["result"].requires_review]
    assert flagged == [], f"unexpectedly flagged for review: {flagged}"


def test_fenced_code_survives_verbatim_in_code_and_sql_categories(results: list[dict[str, Any]]) -> None:
    for item in results:
        if item["entry"]["category"] in ("coding", "sql") and "```" in item["entry"]["text"]:
            original_blocks = item["entry"]["text"].split("```")[1::2]
            for block in original_blocks:
                assert block in item["result"].optimized_text, (
                    f"{item['entry']['id']}: fenced code block was modified"
                )
