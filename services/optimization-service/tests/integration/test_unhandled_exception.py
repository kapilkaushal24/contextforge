"""The catch-all handler (app/api/errors.py:unhandled_exception_handler) must turn any
unexpected exception into the standard error envelope instead of leaking a traceback."""

from typing import NoReturn

from fastapi.testclient import TestClient

from app.api.deps import get_tokenizer_registry
from app.main import create_app


def _boom() -> NoReturn:
    raise RuntimeError("simulated unexpected failure")


def test_unhandled_exception_returns_standard_error_envelope() -> None:
    app = create_app()
    app.dependency_overrides[get_tokenizer_registry] = _boom
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/api/v1/optimize",
        json={
            "text": "hello world",
            "platform": "chatgpt",
            "mode": "balanced",
            "privacyPolicy": "cloud_allowed",
        },
    )

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert "request_id" in body["error"]
    # Never leak the actual exception message/type to the client.
    assert "simulated unexpected failure" not in response.text
    assert "RuntimeError" not in response.text
