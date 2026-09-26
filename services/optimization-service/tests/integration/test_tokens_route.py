from fastapi.testclient import TestClient

TEXT = "Please review this code for bugs, especially performance and security."


def estimate(client: TestClient, provider: str) -> dict[str, object]:
    response = client.post("/api/v1/estimate-tokens", json={"text": TEXT, "provider": provider})
    assert response.status_code == 200
    body: dict[str, object] = response.json()
    return body


def test_estimate_tokens_is_always_labeled_estimated_for_every_provider(
    client: TestClient,
) -> None:
    for provider in ("openai", "anthropic", "gemini", "generic"):
        body = estimate(client, provider)
        assert body["method"] == "estimated"
        assert body["provider"] == provider
        assert isinstance(body["tokens"], int) and body["tokens"] > 0


def test_estimate_tokens_differs_by_provider_tokenizer(client: TestClient) -> None:
    counts = {p: estimate(client, p)["tokens"] for p in ("openai", "anthropic", "generic")}
    assert counts["anthropic"] != counts["generic"] or counts["openai"] != counts["generic"]


def test_estimate_tokens_rejects_unknown_provider(client: TestClient) -> None:
    response = client.post("/api/v1/estimate-tokens", json={"text": TEXT, "provider": "nope"})
    assert response.status_code == 422


def test_optimize_reports_estimated_cost_saved_for_redundant_prompt(client: TestClient) -> None:
    response = client.post(
        "/api/v1/optimize",
        json={
            "text": "Use PostgreSQL for the database. Add tests. Use PostgreSQL for the database.",
            "platform": "chatgpt",
            "mode": "balanced",
            "privacyPolicy": "cloud_allowed",
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["tokensSaved"] > 0
    assert body["estimatedCostSaved"] > 0
    assert body["reductionPercentage"] > 0


def test_optimize_uses_generic_tokenizer_for_unmapped_platform(client: TestClient) -> None:
    response = client.post(
        "/api/v1/optimize",
        json={
            "text": TEXT,
            "platform": "brand-new-ai-tool",
            "mode": "balanced",
            "privacyPolicy": "cloud_allowed",
        },
    )

    assert response.status_code == 200
    assert response.json()["originalTokens"] > 0


def test_optimize_response_exposes_validation_scores_and_reasons(client: TestClient) -> None:
    response = client.post(
        "/api/v1/optimize",
        json={
            "text": "Could you please review this function? Use PostgreSQL. Add tests.",
            "platform": "chatgpt",
            "mode": "balanced",
            "privacyPolicy": "cloud_allowed",
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["semanticSimilarity"] == 1.0
    assert body["constraintPreservation"] == 1.0
    assert body["confidence"] >= 0.85 and body["requiresReview"] is False
    assert body["reviewReasons"] == []


def test_validate_endpoint_flags_dropped_negation_with_reasons(client: TestClient) -> None:
    response = client.post(
        "/api/v1/validate",
        json={
            "originalText": "Write a parser that must not use eval and returns at most 10 keys.",
            "optimizedText": "Write a parser that must use eval and returns at most 10 keys.",
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert "missing_negations" in body["issues"]
    assert body["confidence"] <= 0.5


def test_validate_endpoint_scores_identical_text_as_perfect(client: TestClient) -> None:
    response = client.post(
        "/api/v1/validate",
        json={"originalText": "Same text here.", "optimizedText": "Same text here."},
    )

    assert response.json() == {
        "semanticSimilarity": 1.0,
        "constraintPreservation": 1.0,
        "confidence": 1.0,
        "issues": [],
    }
