from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_application


@pytest.fixture
def client() -> TestClient:
    app = create_application()
    return TestClient(app)


def test_ingest_endpoint_limits_message_size(client: TestClient) -> None:
    response = client.post(
        "/ingest/",
        json={
            "channel": "web",
            "sender": "user",
            "content": "x" * 7000,
        },
    )
    assert response.status_code == 400
    assert "limite" in response.json()["detail"].lower()


def test_channels_endpoint_limits_message_size(client: TestClient) -> None:
    payload = {"content": "x" * 6001, "user_id": "user"}
    response = client.post("/channels/web", json=payload)
    assert response.status_code == 400


def test_webhook_endpoint_limits_message_size(client: TestClient) -> None:
    payload = {"from": "123", "message": "x" * 6001}
    response = client.post("/webhooks/whatsapp", json=payload)
    assert response.status_code == 400
