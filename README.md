# AI Token Optimizer

Chrome extension + backend service that estimates and reduces token usage in prompts sent to
AI chat tools, while preserving user intent — privacy-first, provider-agnostic, built to grow
into an enterprise product.

**Status:** Phases 0–12 complete — planning docs, shared contracts, a buildable Chrome extension
shell (with dynamic AI-platform detection, ADR-009), and a FastAPI backend with deterministic optimization.
Testing/evaluation (Phase 13) is next. See
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
