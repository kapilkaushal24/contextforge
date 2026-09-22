"""Prometheus metrics (§23 observability principle). Module-level singletons — created
once per process regardless of how many times `create_app()` runs (tests call it many
times), which is what avoids prometheus_client's "duplicated timeseries" error.

Every metric here is wired to something the code actually measures. Two things
mentioned in docs/architecture/system-overview.md are deliberately NOT implemented:
`cache_hit_rate` (no cache exists yet — Redis is still Phase 14+; a metric that always
reads zero would be misleading, not honest) and a separate `provider_errors` counter
(folded into `llm_requests_total{outcome="error"}` instead of a redundant metric name).
"""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

optimize_requests_total = Counter(
    "optimize_requests_total",
    "Completed /optimize requests.",
    labelnames=("mode", "outcome"),  # outcome: success | error
)

optimize_latency_seconds = Histogram(
    "optimize_latency_seconds",
    "End-to-end /optimize pipeline latency.",
    labelnames=("mode",),
)

token_reduction_percentage = Histogram(
    "token_reduction_percentage",
    "Reduction percentage achieved per successful optimization.",
    buckets=(0, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100),
)

semantic_validation_failures_total = Counter(
    "semantic_validation_failures_total",
    "Optimizations where the semantic validator's confidence fell below the "
    "configured threshold (requires_review).",
)

llm_requests_total = Counter(
    "llm_requests_total",
    "Calls to the configured LLM provider from the semantic compression strategy.",
    labelnames=("outcome",),  # success | error
)

llm_latency_seconds = Histogram(
    "llm_latency_seconds",
    "Latency of calls to the configured LLM provider.",
)


def render_metrics() -> bytes:
    return generate_latest()


METRICS_CONTENT_TYPE = CONTENT_TYPE_LATEST
