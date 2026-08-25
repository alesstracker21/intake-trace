from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.dependencies import get_pipeline
from app.main import app
from app.models import ExecutionEnvelope


class StubPipeline:
    async def process(self, request):
        return ExecutionEnvelope(
            intake_id=request.intake_id or "INT-TEST",
            source=None,
            trace_id="0" * 32,
            processing_status="FAILED",
            result=None,
            errors=[
                {
                    "code": "INVALID_INPUT",
                    "message": "The raw intake does not match the selected channel contract.",
                    "retryable": False,
                }
            ],
        )


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["model"] == "gemini-3.7-flash"


def test_intake_endpoint_maps_invalid_input_to_400():
    app.dependency_overrides[get_pipeline] = lambda: StubPipeline()
    try:
        with TestClient(app) as client:
            response = client.post(
                "/v1/intakes",
                json={"intake_id": "INT-BAD", "channel": "voicemail", "payload": "bad"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["errors"][0]["code"] == "INVALID_INPUT"


def test_request_validation_error_is_safe():
    with TestClient(app) as client:
        response = client.post(
            "/v1/intakes", json={"channel": "web_form", "payload": "not-an-object"}
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    assert "not-an-object" not in response.text
