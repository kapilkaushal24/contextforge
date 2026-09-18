# ADR-002: FastAPI + Clean Architecture for the Backend

## Context
The optimization backend needs async I/O (calling LLM providers), strong request/response
typing (Pydantic), and a structure that keeps AI/business logic independent of the web
framework and database, so providers/tokenizers/strategies can be swapped without touching the
API layer.

## Decision
Use FastAPI + Pydantic v2 + async SQLAlchemy 2.x, structured as Clean Architecture layers
(`api` → `application` → `domain` ← `infrastructure`) inside `services/optimization-service`,
per [folder-structure.md](../architecture/folder-structure.md). Domain layer has zero
framework dependencies.

## Alternatives considered
- **Django/DRF** — rejected: heavier, sync-first ORM friction with async provider calls,
  less natural fit for a service-oriented, framework-light domain layer.
- **Flask** — rejected: no native async, no built-in Pydantic validation/OpenAPI generation.
- **Monolithic script-style FastAPI app (routes call DB/providers directly)** — rejected:
  violates the "no business logic in API routes" coding rule and makes providers/tokenizers
  hard to swap or unit-test in isolation.

## Consequences
- More upfront structure (interfaces, DI wiring) than a minimal FastAPI app — justified by the
  requirement to swap providers/tokenizers/strategies without touching call sites.
- Every API route is a thin controller delegating to an application-layer use case.
- Domain interfaces (`ITokenizer`, `IAIProvider`, `IOptimizationStrategy`, etc.) are defined in
  `domain`; concrete implementations live in `infrastructure` or `packages/*`.
