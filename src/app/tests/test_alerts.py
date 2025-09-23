from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.app.main import create_application
from src.app.services.alerts import AlertPayload


@pytest.mark.asyncio
async def test_alertmanager_webhook(monkeypatch) -> None:
    app = create_application()
    client = TestClient(app)

    received = []

    async def fake_forward(payload: AlertPayload):
        received.append(payload)

    monkeypatch.setattr("src.app.routers.alerts.forward_alerts_to_whatsapp", fake_forward)

    response = client.post(
        "/alerts/alertmanager",
        json={
            "alerts": [
                {
                    "status": "firing",
                    "labels": {"severity": "critical"},
                    "annotations": {"summary": "Test", "description": "Desc"},
                }
            ]
        },
    )

    assert response.status_code == 202
    assert received
