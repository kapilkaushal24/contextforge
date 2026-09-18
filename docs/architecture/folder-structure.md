# Enterprise Repository Structure

```
ai-token-optimizer/
├── apps/
│   ├── chrome-extension/        # the browser extension (see chrome-extension.md)
│   └── api/                     # thin API gateway app, if split from optimization-service
│
├── services/
│   ├── optimization-service/    # FastAPI: the core optimization backend
│   │   ├── app/
│   │   │   ├── api/             # routers, DTOs — no business logic here
│   │   │   ├── application/     # use cases / orchestration (the pipeline)
│   │   │   ├── domain/          # entities, value objects, interfaces (no framework deps)
│   │   │   ├── infrastructure/  # DB, Redis, provider clients — implements domain interfaces
│   │   │   ├── ml/               # tokenizers, strategies, model router
│   │   │   ├── security/         # authn/z, PII detection, injection defense
│   │   │   ├── observability/    # logging, metrics, tracing setup
│   │   │   └── config/           # settings per environment
│   │   ├── tests/{unit,integration,evaluation,security}/
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   └── analytics-service/       # future: usage/cost analytics, separate from hot path
│
├── packages/                    # shared code, importable by services/apps
│   ├── contracts/                # OpenAPI/JSON-schema shared request/response contracts
│   ├── tokenizers/                # tokenizer implementations, shareable
│   ├── optimization-core/        # strategies, pipeline, pure domain logic
│   ├── provider-adapters/        # IAIProvider implementations
│   └── shared/                    # cross-cutting utils (errors, types)
│
├── ml/                            # offline: datasets, evaluation harness, experiments
│   ├── datasets/ evaluation/ experiments/ models/ notebooks/ pipelines/
│
├── infrastructure/
│   ├── docker/ terraform/ kubernetes/ monitoring/
│
├── docs/
│   ├── architecture/ api/ security/ decisions/ product/
│
├── scripts/
├── .github/workflows/
├── docker-compose.yml
├── README.md
└── LICENSE
```

## Why each top-level directory exists

- **apps/** — deployable, user-facing entry points (browser extension, gateway). Nothing
  reusable should live only here.
- **services/** — independently deployable backend services. `optimization-service` is the
  core; `analytics-service` is split out early so analytics load never affects optimization
  latency.
- **packages/** — code shared between services/apps without duplicating business logic
  (explicitly forbidden by the coding rules). `optimization-core` has zero framework
  dependencies so it's testable and portable (e.g., could run locally for `LOCAL_ONLY` policy).
- **ml/** — offline concerns (datasets, evaluation, experiments) kept out of the runtime
  services so the evaluation framework can evolve independently of production code.
- **infrastructure/** — deployment concerns isolated from application code.
- **docs/** — living architecture/product/decision record, kept next to the code it describes.

## Clean Architecture layering inside `optimization-service`

`api` (interface) → `application` (use cases) → `domain` (entities/interfaces, no deps) ←
`infrastructure` (implements domain interfaces: DB, Redis, provider SDKs). Dependencies point
inward; `domain` never imports from `infrastructure` or `api`.
