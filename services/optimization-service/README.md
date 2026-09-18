# optimization-service

FastAPI backend implementing the `/api/v1/*` surface described in
[docs/api/contracts.md](../../docs/api/contracts.md). This is the **Phase 5 skeleton**: routing,
DTOs, error handling, request correlation, and Clean Architecture layering are real and tested;
the optimization logic behind `/optimize`, `/analyze`, `/estimate-tokens`, and `/validate` is a
documented placeholder (word-count-based, no LLM calls) until Phases 6-9 replace it strategy by
strategy — the request/response contracts and route code do not change when they do.

## Layering

`api/` (routes + Pydantic DTOs) → `application/` (use cases, e.g. `optimize_use_case.py`) →
`optimization_core` (the shared domain package: entities + `Protocol` interfaces, from
`packages/optimization-core`). Routes never contain business logic; they map DTOs to/from domain
objects and call a use case.

## Develop

```bash
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e "../../packages/optimization-core"   # domain package
./.venv/Scripts/python.exe -m pip install -e ".[dev]"                              # this service
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

Interactive API docs: http://localhost:8000/docs

```bash
./.venv/Scripts/python.exe -m pytest        # unit + integration
./.venv/Scripts/python.exe -m mypy app
```

## Config

Copy `.env.example` to `.env` and adjust. Nothing is hard-coded (§31) — see
`app/config/settings.py`. `AITO_REQUIRE_API_KEY` is `false` by default for local dev.

## Not yet implemented

- Real optimization strategies (Phases 6-9) — see the docstring at the top of each
  `app/application/*_use_case.py` file for exactly what each placeholder does and what replaces
  it.
- Database/Redis (no persistence needed yet — settings are in-memory, usage stats are zeroed).
- Real `IAIProvider`/`ITokenizer` implementations (Phase 7/8) — `/providers` and `/models`
  honestly return empty lists rather than fabricated data.
