from fastapi.testclient import TestClient


def test_optimize_happy_path(client: TestClient) -> None:
    response = client.post(
        "/api/v1/optimize",
        json={
            "text": "Please review this code for bugs.",
            "platform": "chatgpt",
            "mode": "balanced",
            "privacyPolicy": "cloud_allowed",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["optimizedText"] == "Please review this code for bugs."
    assert body["tokensSaved"] == 0
    assert body["requiresReview"] is False
    assert body["confidence"] == 1.0


def test_optimize_rejects_empty_text_with_error_envelope(client: TestClient) -> None:
    response = client.post(
        "/api/v1/optimize",
        json={"text": "", "platform": "chatgpt", "mode": "balanced", "privacyPolicy": "cloud_allowed"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "request_id" in body["error"]


def test_optimize_accepts_an_unrecognized_platform(client: TestClient) -> None:
    """Platform is an open string end-to-end (ADR-009) — the backend must not reject
    a platform id it doesn't recognize."""
    response = client.post(
        "/api/v1/optimize",
        json={
            "text": "hello world",
            "platform": "some-new-ai-tool",
            "mode": "balanced",
            "privacyPolicy": "cloud_allowed",
        },
    )

    assert response.status_code == 200
