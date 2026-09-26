FROM python:3.14-slim AS base

WORKDIR /srv

# optimization-core is a local path dependency (see README) — copy it in before the
# service itself so Docker layer caching still works when only app/ changes.
COPY packages/optimization-core /srv/packages/optimization-core
COPY packages/tokenizers /srv/packages/tokenizers
COPY packages/provider-adapters /srv/packages/provider-adapters
COPY services/optimization-service/pyproject.toml /srv/pyproject.toml
RUN pip install --no-cache-dir /srv/packages/optimization-core "/srv/packages/tokenizers[openai]" /srv/packages/provider-adapters \
    && pip install --no-cache-dir -e /srv --no-deps \
    && pip install --no-cache-dir fastapi "uvicorn[standard]" pydantic pydantic-settings prometheus-client

COPY services/optimization-service/app /srv/app

# Runs as a non-root user (§12 security principle) — the image needs no write access
# to anything outside its own process, so there's no reason to run as root.
RUN useradd --no-create-home --shell /usr/sbin/nologin appuser
USER appuser

EXPOSE 8000

# No curl in the slim base image (and installing it would add a layer just for this) —
# a one-line Python request against the unauthenticated /healthz route is enough.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
