# optimization-core

Pure domain layer for the optimization backend: entities (`entities.py`) and interfaces
(`interfaces.py`) as `typing.Protocol`s. Zero framework dependencies (no FastAPI, no
SQLAlchemy, no Pydantic) — this is deliberate (ADR-002) so tokenizers, providers, and
strategies can be swapped without touching call sites, and so the domain layer is trivially
unit-testable.

Concrete implementations live elsewhere:
- `packages/tokenizers` — `ITokenizer` implementations (Phase 7).
- `packages/provider-adapters` — `IAIProvider` implementations (Phase 8).
- `services/optimization-service/app/infrastructure` — DB/Redis-backed pieces (Phase 5+).

## Develop

```bash
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e ".[dev]"   # Windows
./.venv/bin/python -m pip install -e ".[dev]"            # macOS/Linux
pytest
mypy src
```
