# ADR-012: Observability Scope — Prometheus Metrics + Log-Correlated Timing, No Tracing Backend

## Context
docs/product/development-phases.md's Phase 12 calls for "structured logging, metrics,
tracing." Structured JSON logging and request-ID correlation already existed (Phase 5).
Metrics and tracing needed a real decision: full distributed tracing (OpenTelemetry SDK
+ a collector like Jaeger/Tempo) is standard infrastructure, but this service has no
deployed observability backend, and adding an SDK with no exporter target would be
untested, unverifiable ceremony — exactly what §38 warns against ("cheapest safe
transformation first" applies to engineering effort too, not just token optimization).

## Decision
- **Metrics**: `prometheus_client`, exposed at `GET /metrics` (outside `/api/v1`, never
  gated by the API key — scraping is a network-level concern, not a request-auth one).
  Every metric is wired to something the code actually measures:
  `optimize_requests_total{mode,outcome}`, `optimize_latency_seconds{mode}`,
  `token_reduction_percentage`, `semantic_validation_failures_total`,
  `llm_requests_total{outcome}`, `llm_latency_seconds`.
- **Deliberately not implemented**: `cache_hit_rate` (no cache exists — Redis is still
  deferred past Phase 5's original scope) and a separate `provider_errors` metric
  (folded into `llm_requests_total{outcome="error"}` rather than a redundant name). A
  metric with no real signal behind it is worse than no metric — consistent with the
  project's standing rule against fabricated data (`/providers` and `/models` return
  empty lists rather than invented ones, ADR-003's honest-`estimated`-label rule).
- **Tracing, scoped down to log-correlated stage timings**: `run_optimization` times
  each pipeline stage (deterministic, structural, LLM, validation) and emits one
  structured log line per request — `{"stage_ms": {...}, "total_ms": ..., request_id via
  the existing middleware}`. This answers "where did this request's latency go" without
  standing up trace-collection infrastructure, and it's real, tested, and greppable
  today rather than instrumented-but-unexercised.
- **Closed a real gap found while wiring this**: there was no catch-all exception
  handler. An unexpected bug in a route or dependency would have returned FastAPI's
  default response (a raw traceback in dev, an opaque 500 in prod) instead of the
  project's consistent `{error: {code, message, request_id}}` envelope. Added
  `unhandled_exception_handler` (`app/api/errors.py`): logs the real exception
  server-side with `request_id`, returns a generic `INTERNAL_ERROR` message that never
  leaks exception details to the client.

## Alternatives considered
- **OpenTelemetry SDK with an OTLP exporter pointed at nothing** — rejected: would
  compile and run, but there is nothing to verify it against; untested infrastructure
  code is a liability, not an asset.
- **Custom span/trace-id propagation format** — rejected: reinvents a wheel
  OpenTelemetry already standardizes; if/when a real tracing backend is deployed, that's
  the point to adopt OTel properly rather than migrate a bespoke format.
- **Track `optimize_failures_total` as a distinct metric from the generic exception
  handler's log line** — considered; the exception handler's structured log
  (`unhandled exception`, with `request_id`) already gives this signal at effectively
  the same granularity a counter would, and 500s should be rare enough that log-based
  alerting is sufficient before this graduates to a dedicated metric.

## Consequences
- If/when a real tracing backend (Jaeger, Tempo, a hosted APM) is provisioned, the
  per-stage timing data already exists in log form; migrating to OpenTelemetry spans is
  additive, not a rewrite of the instrumentation points.
- Prometheus metric objects are module-level singletons (`app/observability/metrics.py`)
  specifically so `create_app()` — called once per test file, many times per test run —
  never triggers `prometheus_client`'s "duplicated timeseries" registration error.
- `/metrics` being unauthenticated means anyone who can reach the service's network can
  scrape it; in a real deployment this is normally handled by network policy (internal
  network only, or a reverse-proxy rule), not application-level auth — matching how
  Prometheus scraping is conventionally deployed.
