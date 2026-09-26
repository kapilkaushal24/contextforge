#!/usr/bin/env python3
"""Evaluation harness for the optimization pipeline (MVP roadmap item 2,
docs/product/mvp-scope.md). Runs the benchmark dataset against a *live*
optimization-service instance over HTTP and reports the metrics that matter:

  - token reduction (%) — the core value proposition
  - semantic preservation — confidence / semanticSimilarity / constraintPreservation
    from the deterministic validator (docs/decisions/ADR-006)
  - latency (ms, client-observed wall clock)
  - estimated cost saved

Deliberately NOT measured here: "task success" (did the optimized prompt still get a
correct answer from a downstream model) and "hallucination risk". Both would require
an LLM-as-judge or a human rater — the project has already decided against that as a
default (see ADR-006's rejection of LLM-as-judge and ADR-011/012's stance against
metrics with no real signal behind them). If/when that's worth the cost, it belongs
here as an additional, clearly-labeled optional pass, not a silent assumption baked
into these numbers.

Zero third-party dependencies on purpose — this is an offline/ml-tooling script
(folder-structure.md: `ml/` stays decoupled from the runtime services), runnable with
nothing but the standard library, against a `docker compose up` or local `uvicorn`
instance of optimization-service.

Usage:
    python ml/evaluation/run_eval.py
    python ml/evaluation/run_eval.py --base-url http://localhost:8000 --mode aggressive
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DEFAULT_DATASET = Path(__file__).parent / "datasets" / "benchmark_prompts.jsonl"
DEFAULT_RESULTS_DIR = Path(__file__).parent / "results"


@dataclass
class EvalRecord:
    id: str
    category: str
    mode: str
    expect_reduction: bool
    original_tokens: int
    optimized_tokens: int
    reduction_percentage: float
    confidence: float
    requires_review: bool
    review_reasons: list[str]
    estimated_cost_saved: float
    latency_ms: float
    error: str | None = None


def load_dataset(path: Path) -> list[dict[str, Any]]:
    entries = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def call_optimize(
    base_url: str, text: str, mode: str, privacy_policy: str, platform: str, timeout: float
) -> tuple[dict[str, Any], float]:
    body = json.dumps(
        {"text": text, "platform": platform, "mode": mode, "privacyPolicy": privacy_policy}
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/api/v1/optimize",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read())
    latency_ms = (time.perf_counter() - started) * 1000
    return payload, latency_ms


def run(
    dataset: list[dict[str, Any]],
    base_url: str,
    privacy_policy: str,
    platform: str,
    mode_override: str | None,
    timeout: float,
) -> list[EvalRecord]:
    records: list[EvalRecord] = []
    for entry in dataset:
        mode = mode_override or entry["mode"]
        try:
            payload, latency_ms = call_optimize(
                base_url, entry["text"], mode, privacy_policy, platform, timeout
            )
        except (urllib.error.URLError, TimeoutError) as exc:
            records.append(
                EvalRecord(
                    id=entry["id"],
                    category=entry["category"],
                    mode=mode,
                    expect_reduction=entry["expect_reduction"],
                    original_tokens=0,
                    optimized_tokens=0,
                    reduction_percentage=0.0,
                    confidence=0.0,
                    requires_review=False,
                    review_reasons=[],
                    estimated_cost_saved=0.0,
                    latency_ms=0.0,
                    error=str(exc),
                )
            )
            continue

        records.append(
            EvalRecord(
                id=entry["id"],
                category=entry["category"],
                mode=mode,
                expect_reduction=entry["expect_reduction"],
                original_tokens=payload["originalTokens"],
                optimized_tokens=payload["optimizedTokens"],
                reduction_percentage=payload["reductionPercentage"],
                confidence=payload["confidence"],
                requires_review=payload["requiresReview"],
                review_reasons=payload["reviewReasons"],
                estimated_cost_saved=payload["estimatedCostSaved"],
                latency_ms=latency_ms,
            )
        )
    return records


def summarize(records: list[EvalRecord]) -> dict[str, Any]:
    ok = [r for r in records if r.error is None]
    failed = [r for r in records if r.error is not None]
    reducible = [r for r in ok if r.expect_reduction]
    baseline = [r for r in ok if not r.expect_reduction]

    def avg(values: list[float]) -> float:
        return round(statistics.mean(values), 2) if values else 0.0

    return {
        "total_prompts": len(records),
        "failed_requests": len(failed),
        "avg_reduction_percentage_reducible_prompts": avg([r.reduction_percentage for r in reducible]),
        "avg_confidence": avg([r.confidence for r in ok]),
        "requires_review_count": sum(1 for r in ok if r.requires_review),
        "baseline_prompts_unexpectedly_shrunk": [
            r.id for r in baseline if r.reduction_percentage > 0
        ],
        "avg_latency_ms": avg([r.latency_ms for r in ok]),
        "p95_latency_ms": round(_percentile([r.latency_ms for r in ok], 95), 2) if ok else 0.0,
        "total_estimated_cost_saved_usd": round(sum(r.estimated_cost_saved for r in ok), 6),
        "by_category": _by_category(ok),
    }


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((pct / 100) * (len(ordered) - 1)))
    return ordered[index]


def _by_category(records: list[EvalRecord]) -> dict[str, dict[str, float]]:
    categories = sorted({r.category for r in records})
    result = {}
    for category in categories:
        subset = [r for r in records if r.category == category]
        result[category] = {
            "count": len(subset),
            "avg_reduction_percentage": round(
                statistics.mean([r.reduction_percentage for r in subset]), 2
            ),
            "avg_confidence": round(statistics.mean([r.confidence for r in subset]), 2),
        }
    return result


def print_report(records: list[EvalRecord], summary: dict[str, Any]) -> None:
    print(f"{'id':<16} {'category':<14} {'mode':<12} {'reduce%':>8} {'conf':>6} {'review':>7} {'ms':>8}")
    for r in records:
        if r.error:
            print(f"{r.id:<16} {r.category:<14} {r.mode:<12} {'ERROR':>8}  {r.error}")
            continue
        print(
            f"{r.id:<16} {r.category:<14} {r.mode:<12} {r.reduction_percentage:>7.1f}% "
            f"{r.confidence:>6.2f} {r.requires_review!s:>7} {r.latency_ms:>7.1f}"
        )
    print()
    print(json.dumps(summary, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--privacy-policy", default="cloud_allowed", choices=["cloud_allowed", "local_only"])
    parser.add_argument("--platform", default="generic")
    parser.add_argument("--mode", default=None, help="override every prompt's mode (default: use dataset's per-prompt mode)")
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()

    dataset = load_dataset(args.dataset)
    records = run(dataset, args.base_url, args.privacy_policy, args.platform, args.mode, args.timeout)
    summary = summarize(records)
    print_report(records, summary)

    args.results_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.results_dir / f"eval-{time.strftime('%Y%m%dT%H%M%S')}.json"
    out_path.write_text(
        json.dumps({"summary": summary, "records": [asdict(r) for r in records]}, indent=2),
        encoding="utf-8",
    )
    print(f"\nWrote {out_path}")

    return 1 if summary["failed_requests"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
