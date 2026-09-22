from fastapi.testclient import TestClient

OPTIMIZE_BODY = {
    "text": "Could you please review this function? Use PostgreSQL. Use PostgreSQL.",
    "platform": "chatgpt",
    "mode": "balanced",
    "privacyPolicy": "cloud_allowed",
}


def test_metrics_endpoint_returns_prometheus_text_format(client: TestClient) -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")


def test_metrics_endpoint_is_not_gated_by_api_key() -> None:
    from app.config.settings import Settings, get_settings
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, require_api_key=True, api_key="secret"  # type: ignore[call-arg]
    )
    client = TestClient(app)
    assert client.get("/metrics").status_code == 200


def _metric_value(body: str, name_with_labels: str) -> float:
    for line in body.splitlines():
        if line.startswith(name_with_labels + " "):
            return float(line.rsplit(" ", 1)[1])
    return 0.0


def test_optimize_request_is_reflected_in_metrics(client: TestClient) -> None:
    metric = 'optimize_requests_total{mode="balanced",outcome="success"}'
    before = _metric_value(client.get("/metrics").text, metric)

    client.post("/api/v1/optimize", json=OPTIMIZE_BODY)

    body = client.get("/metrics").text
    assert _metric_value(body, metric) == before + 1
    assert "optimize_latency_seconds" in body
    assert "token_reduction_percentage" in body
