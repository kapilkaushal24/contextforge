"""Phase 11: detected PII/secrets must block cloud LLM routing by default, even when
cloud is otherwise allowed and the LLM is enabled — see optimization_core.pii and
ModelRouter.route's `contains_sensitive_content` gate."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from optimization_core import ModelRouter, RouterPolicy
from optimization_core.strategies import SemanticCompressionStrategy

from app.api.deps import get_model_router
from app.main import create_app

CLEAN_TEXT = "Could you please summarize this quarterly report for the board?"
EMAIL_TEXT = "Could you please draft a reply to jane.doe@example.com about the invoice?"
# Concatenated rather than a literal contiguous string — an obviously-fake fixture that
# satisfies our regex's *shape*, kept from visually matching real-token scanners.
API_KEY_TEXT = (
    "Here is my key " + "sk-" + "abcdefghijklmnopqrstuvwx" + ", please explain what scope it needs."
)
REWRITE = "a short rewrite"


class RecordingProvider:
    provider_id = "recording"

    def __init__(self) -> None:
        self.calls = 0

    async def complete(self, *, system: str, user: str, max_tokens: int) -> str:
        self.calls += 1
        return REWRITE


@pytest.fixture()
def provider() -> RecordingProvider:
    return RecordingProvider()


@pytest.fixture()
def client(provider: RecordingProvider) -> Iterator[TestClient]:
    app = create_app()
    router = ModelRouter(
        SemanticCompressionStrategy(provider),
        RouterPolicy(llm_enabled=True, cost_optimization_enabled=False, block_pii_from_cloud=True),
    )
    app.dependency_overrides[get_model_router] = lambda: router
    yield TestClient(app)


def optimize(client: TestClient, text: str) -> dict[str, object]:
    response = client.post(
        "/api/v1/optimize",
        json={
            "text": text,
            "platform": "chatgpt",
            "mode": "balanced",
            "privacyPolicy": "cloud_allowed",
        },
    )
    assert response.status_code == 200
    body: dict[str, object] = response.json()
    return body


def test_clean_prompt_uses_the_llm_and_reports_no_categories(
    client: TestClient, provider: RecordingProvider
) -> None:
    body = optimize(client, CLEAN_TEXT)
    assert provider.calls == 1
    assert body["sensitiveContentCategories"] == []


def test_email_blocks_the_llm_and_is_reported(
    client: TestClient, provider: RecordingProvider
) -> None:
    body = optimize(client, EMAIL_TEXT)
    assert provider.calls == 0
    assert body["sensitiveContentCategories"] == ["email"]
    assert body["optimizedText"] != REWRITE


def test_api_key_blocks_the_llm_and_is_reported(
    client: TestClient, provider: RecordingProvider
) -> None:
    body = optimize(client, API_KEY_TEXT)
    assert provider.calls == 0
    assert "api_key" in body["sensitiveContentCategories"]  # type: ignore[operator]


def test_categories_are_reported_even_when_the_llm_is_disabled() -> None:
    # The detector itself does not depend on LLM optimization being on — a deployment
    # with the LLM off entirely still surfaces what was found.
    body = optimize(TestClient(create_app()), EMAIL_TEXT)
    assert body["sensitiveContentCategories"] == ["email"]
