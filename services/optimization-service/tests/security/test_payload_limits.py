"""Input validation at the API boundary (§12 security principle: never trust the
network). Every /api/v1 route uses Pydantic DTOs (app/api/v1/schemas.py) with explicit
length bounds; these tests exercise the boundary conditions directly against the API,
not just the schema in isolation."""

from fastapi.testclient import TestClient


def test_oversized_text_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/optimize",
        json={
            "text": "a" * 100_001,
            "platform": "chatgpt",
            "mode": "balanced",
            "privacyPolicy": "cloud_allowed",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_max_length_text_is_accepted(client: TestClient) -> None:
    response = client.post(
        "/api/v1/optimize",
        json={
            "text": "a" * 100_000,
            "platform": "chatgpt",
            "mode": "balanced",
            "privacyPolicy": "cloud_allowed",
        },
    )
    assert response.status_code == 200


def test_empty_text_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/optimize",
        json={
            "text": "",
            "platform": "chatgpt",
            "mode": "balanced",
            "privacyPolicy": "cloud_allowed",
        },
    )
    assert response.status_code == 422


def test_missing_required_field_is_rejected(client: TestClient) -> None:
    response = client.post("/api/v1/optimize", json={"platform": "chatgpt", "mode": "balanced"})
    assert response.status_code == 422


def test_invalid_mode_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/optimize",
        json={
            "text": "hello world",
            "platform": "chatgpt",
            "mode": "not_a_real_mode",
            "privacyPolicy": "cloud_allowed",
        },
    )
    assert response.status_code == 422


def test_malformed_json_is_rejected_not_500(client: TestClient) -> None:
    response = client.post(
        "/api/v1/optimize",
        content=b"{not valid json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_wrong_type_for_a_field_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/optimize",
        json={
            "text": 12345,
            "platform": "chatgpt",
            "mode": "balanced",
            "privacyPolicy": "cloud_allowed",
        },
    )
    assert response.status_code == 422


def test_oversized_validate_fields_are_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/validate",
        json={"originalText": "a" * 100_001, "optimizedText": "short"},
    )
    assert response.status_code == 422
