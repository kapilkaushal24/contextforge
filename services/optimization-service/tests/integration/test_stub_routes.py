"""Coverage for /analyze, /feedback, /providers, /models, /settings, and /usage.

Persisted analytics remain a deliberate placeholder; tests pin that response shape until
the storage implementation is defined.
"""

from fastapi.testclient import TestClient


def test_analyze_classifies_code_prompt(client: TestClient) -> None:
    response = client.post(
        "/api/v1/analyze", json={"text": "def foo(x):\n    return x + 1\n\nclass Bar:\n    pass"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["promptType"] == "code"
    assert body["estimatedTokens"] > 0
    assert body["hasDetectedRedundancy"] is False


def test_analyze_classifies_general_prompt(client: TestClient) -> None:
    response = client.post("/api/v1/analyze", json={"text": "Write a short poem about the ocean."})
    assert response.status_code == 200
    assert response.json()["promptType"] == "general"


def test_analyze_rejects_empty_text(client: TestClient) -> None:
    assert client.post("/api/v1/analyze", json={"text": ""}).status_code == 422


def test_feedback_is_accepted(client: TestClient) -> None:
    response = client.post(
        "/api/v1/feedback",
        json={"requestId": "req-123", "rating": "helpful", "reason": None},
    )
    assert response.status_code == 202
    assert response.json() == {"accepted": True}


def test_feedback_without_optional_reason(client: TestClient) -> None:
    response = client.post(
        "/api/v1/feedback", json={"requestId": "req-124", "rating": "not_helpful"}
    )
    assert response.status_code == 202


def test_feedback_rejects_invalid_rating(client: TestClient) -> None:
    response = client.post("/api/v1/feedback", json={"requestId": "req-125", "rating": "sort_of"})
    assert response.status_code == 422


def test_providers_reports_supported_provider_availability(client: TestClient) -> None:
    response = client.get("/api/v1/providers")
    assert response.status_code == 200
    assert response.json() == [
        {"id": "openai", "name": "OpenAI", "status": "unavailable"},
        {"id": "anthropic", "name": "Anthropic", "status": "unavailable"},
    ]


def test_models_reports_configured_model_and_pricing(client: TestClient) -> None:
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "gpt-4o-mini",
            "providerId": "openai",
            "name": "gpt-4o-mini",
            "inputPricePer1k": 0.00015,
            "outputPricePer1k": 0.0006,
        }
    ]


def test_get_settings_returns_defaults(client: TestClient) -> None:
    response = client.get("/api/v1/settings")
    assert response.status_code == 200
    body = response.json()
    assert body["defaultMode"] == "balanced"
    assert body["privacyPolicy"] == "cloud_allowed"
    assert body["featureFlags"] == {}


def test_put_settings_updates_and_get_reflects_it(client: TestClient) -> None:
    updated = {
        "defaultMode": "aggressive",
        "privacyPolicy": "local_only",
        "featureFlags": {"context_mode": True},
    }
    put_response = client.put("/api/v1/settings", json=updated)
    assert put_response.status_code == 200
    assert put_response.json() == updated

    get_response = client.get("/api/v1/settings")
    assert get_response.json() == updated


def test_usage_defaults_to_last_seven_days_and_zeroed_summary(client: TestClient) -> None:
    response = client.get("/api/v1/usage")
    assert response.status_code == 200
    body = response.json()
    assert body["totalRequests"] == 0
    assert body["totalTokensSaved"] == 0
    assert body["averageReductionPercentage"] == 0.0
    assert body["estimatedCostSaved"] == 0.0
    assert body["rangeStart"] < body["rangeEnd"]


def test_usage_accepts_explicit_date_range(client: TestClient) -> None:
    response = client.get(
        "/api/v1/usage", params={"range_start": "2026-01-01", "range_end": "2026-01-31"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["rangeStart"] == "2026-01-01"
    assert body["rangeEnd"] == "2026-01-31"


def test_usage_rejects_malformed_date(client: TestClient) -> None:
    response = client.get("/api/v1/usage", params={"range_start": "not-a-date"})
    assert response.status_code == 422
