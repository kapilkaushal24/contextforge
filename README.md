# AI Token Optimizer

Chrome extension + backend service that estimates and reduces token usage in prompts sent to
AI chat tools, while preserving user intent — privacy-first, provider-agnostic, built to grow
into an enterprise product.

**Status:** Phases 0–14 complete. Planning docs, shared contracts, a buildable Chrome extension
shell (with dynamic AI-platform detection, ADR-009), a FastAPI backend with the full optimization
pipeline, 100% line coverage on `provider-adapters` and the backend, an evaluation harness
([ml/evaluation](ml/evaluation)), and CI + a hardened Docker image on Python 3.14 / Node 24
(ADR-013). The MVP is functionally complete; Phase 15 (enterprise features) is post-MVP. See
[docs/product/development-phases.md](docs/product/development-phases.md).

## Quick start

```bash
npm install                 # installs the extension + contracts workspaces
npm run build:contracts
npm run build:extension     # outputs apps/chrome-extension/dist — load it unpacked in Chrome
npm run typecheck
```

Python packages (domain + backend):

```bash
cd packages/optimization-core
python -m venv .venv && ./.venv/Scripts/python.exe -m pip install -e ".[dev]"
./.venv/Scripts/python.exe -m pytest

cd ../../services/optimization-service
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e "../../packages/optimization-core" -e ".[dev]"
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000   # http://localhost:8000/docs
```

Or via Docker (see [services/optimization-service/README.md](services/optimization-service/README.md)):

```bash
docker compose up -d --build   # then curl http://localhost:8000/healthz
```

Evaluation harness (once the backend is running): `python ml/evaluation/run_eval.py` — see
[ml/evaluation/README.md](ml/evaluation/README.md).

## Start here

- [Product Requirements](docs/product/requirements.md)
- [System Overview & Data Flow](docs/architecture/system-overview.md)
- [Chrome Extension Architecture](docs/architecture/chrome-extension.md)
- [AI/ML Architecture & Optimization Pipeline](docs/architecture/ai-ml.md)
- [Security & Privacy](docs/security/privacy-security.md)
- [Repository Structure](docs/architecture/folder-structure.md)
- [Chrome Extension shell](apps/chrome-extension/README.md)
- [Shared TS contracts](packages/contracts/README.md)
- [Python domain interfaces](packages/optimization-core/README.md)
- [Backend API service](services/optimization-service/README.md)
- [Database ERD](docs/architecture/database-erd.md)
- [API Contracts](docs/api/contracts.md)
- [MVP Scope & Roadmap](docs/product/mvp-scope.md)
- [Development Phases](docs/product/development-phases.md)
- [Architecture Decision Records](docs/decisions/ADR-000-index.md)

## Principle

Cheapest safe transformation first: deterministic optimization before structural, structural
before semantic/LLM-assisted. Never optimize purely to minimize tokens at the cost of user
intent. Never silently modify a user's prompt without an explicit Apply.
