from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from optimization_core import ModelRouter, RouterPolicy
from optimization_core.errors import ProviderError
from optimization_core.strategies import SemanticCompressionStrategy

from app.api.deps import get_model_router
from app.main import create_app

LONG = (
    "Could you please write a Python function called parse_config that reads a YAML file "
    "and must not use eval? It should return at most 10 keys."
)
REWRITE = "Write Python parse_config: read YAML, must not use eval, return at most 10 keys."


class FakeProvider:
    provider_id = "fake"

    def __init__(self, reply: str = "", error: Exception | None = None) -> None:
        self.reply, self.error, self.seen_system = reply, error, ""

    async def complete(self, *, system: str, user: str, max_tokens: int) -> str:
        self.seen_system = system
        if self.error:
            raise self.error
        return self.reply


def client_with(provider: FakeProvider) -> Iterator[TestClient]:
    app = create_app()
    router = ModelRouter(
        SemanticCompressionStrategy(provider),
        RouterPolicy(llm_enabled=True, cost_optimization_enabled=False),
    )
    app.dependency_overrides[get_model_router] = lambda: router
    yield TestClient(app)


def post(client: TestClient, text: str = LONG, privacy: str = "cloud_allowed") -> dict[str, object]:
    response = client.post(
        "/api/v1/optimize",
        json={"text": text, "platform": "claude", "mode": "balanced", "privacyPolicy": privacy},
    )
    assert response.status_code == 200
    body: dict[str, object] = response.json()
    return body


@pytest.fixture()
def happy_client() -> Iterator[TestClient]:
    yield from client_with(FakeProvider(REWRITE))


@pytest.fixture()
def failing_client() -> Iterator[TestClient]:
    yield from client_with(FakeProvider(error=ProviderError("HTTP 503")))


def test_llm_rewrite_flows_through_the_api(happy_client: TestClient) -> None:
    body = post(happy_client)

    assert body["optimizedText"] == REWRITE
    assert body["originalText"] == LONG
    assert "semantic_compression" in {c["type"] for c in body["changes"]}  # type: ignore[attr-defined]
    assert body["tokensSaved"] > 0  # type: ignore[operator]


def test_local_only_privacy_never_uses_the_llm(happy_client: TestClient) -> None:
    body = post(happy_client, privacy="local_only")

    assert body["optimizedText"] != REWRITE
    assert "semantic_compression" not in {c["type"] for c in body["changes"]}  # type: ignore[attr-defined]


def test_provider_outage_still_returns_a_usable_result(failing_client: TestClient) -> None:
    body = post(failing_client)

    assert body["optimizedText"]
    assert "semantic_compression" not in {c["type"] for c in body["changes"]}  # type: ignore[attr-defined]


def test_default_app_has_llm_disabled_and_makes_no_network_calls() -> None:
    body = post(TestClient(create_app()))

    assert "semantic_compression" not in {c["type"] for c in body["changes"]}  # type: ignore[attr-defined]
