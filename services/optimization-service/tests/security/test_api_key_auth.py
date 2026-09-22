"""API-key enforcement (app/security/api_key.py). Off by default in dev — these tests
exercise the enforced path explicitly via dependency overrides."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config.settings import Settings, get_settings
from app.main import create_app

OPTIMIZE_BODY = {
    "text": "Review this function for bugs.",
    "platform": "chatgpt",
    "mode": "balanced",
    "privacyPolicy": "cloud_allowed",
}


def _enforced_settings() -> Settings:
    # A plain zero-arg callable: FastAPI re-introspects a dependency override's own
    # signature (overrides can have sub-dependencies), so a `**kwargs`-style function
    # here gets misread as needing extra injected parameters and 422s every request.
    return Settings(_env_file=None, require_api_key=True, api_key="correct-key")  # type: ignore[call-arg]


@pytest.fixture()
def enforced_client() -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_settings] = _enforced_settings
    yield TestClient(app)


def test_request_without_api_key_is_rejected(enforced_client: TestClient) -> None:
    response = enforced_client.post("/api/v1/optimize", json=OPTIMIZE_BODY)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "HTTP_ERROR"


def test_request_with_wrong_api_key_is_rejected(enforced_client: TestClient) -> None:
    response = enforced_client.post(
        "/api/v1/optimize", json=OPTIMIZE_BODY, headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 401


def test_request_with_correct_api_key_succeeds(enforced_client: TestClient) -> None:
    response = enforced_client.post(
        "/api/v1/optimize", json=OPTIMIZE_BODY, headers={"X-API-Key": "correct-key"}
    )
    assert response.status_code == 200


def test_healthz_is_never_gated_by_api_key(enforced_client: TestClient) -> None:
    # /healthz is mounted outside the /api/v1 router (see app/main.py) and must stay
    # reachable for liveness checks even when the API itself requires a key.
    assert enforced_client.get("/healthz").status_code == 200


def test_disabled_by_default_allows_unauthenticated_requests(client: TestClient) -> None:
    response = client.post("/api/v1/optimize", json=OPTIMIZE_BODY)
    assert response.status_code == 200
