FROM python:3.12-slim AS base

WORKDIR /srv

# optimization-core is a local path dependency (see README) — copy it in before the
# service itself so Docker layer caching still works when only app/ changes.
COPY packages/optimization-core /srv/packages/optimization-core
COPY services/optimization-service/pyproject.toml /srv/pyproject.toml
RUN pip install --no-cache-dir /srv/packages/optimization-core \
    && pip install --no-cache-dir -e /srv --no-deps \
    && pip install --no-cache-dir fastapi "uvicorn[standard]" pydantic pydantic-settings

COPY services/optimization-service/app /srv/app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
