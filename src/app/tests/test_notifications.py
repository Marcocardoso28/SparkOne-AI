from __future__ import annotations

import pytest

from src.app.workers.scheduler import _notify_whatsapp
from src.app.core.metrics import WHATSAPP_NOTIFICATION_COUNTER, FALLBACK_NOTIFICATION_COUNTER
from src.app.config import Settings


class DummyService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.should_fail = False

    async def send_text(self, to: str, message: str) -> None:
        if self.should_fail:
            raise RuntimeError("fail")
        self.calls.append((to, message))


@pytest.mark.asyncio
async def test_notify_whatsapp_success(monkeypatch) -> None:
    service = DummyService()
    settings = Settings(whatsapp_notify_numbers="5511999999999, 5511888888888")

    monkeypatch.setattr("src.app.workers.scheduler.get_settings", lambda: settings)
    monkeypatch.setattr("src.app.workers.scheduler.get_whatsapp_service", lambda: service)

    WHATSAPP_NOTIFICATION_COUNTER.labels(status="success")._value.set(0)  # type: ignore[attr-defined]

    await _notify_whatsapp("Resumo do dia")

    assert len(service.calls) == 2
    assert WHATSAPP_NOTIFICATION_COUNTER.labels(status="success")._value.get() == 2  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_notify_whatsapp_failure(monkeypatch) -> None:
    service = DummyService()
    service.should_fail = True
    settings = Settings(whatsapp_notify_numbers="5511999999999", fallback_email="test@example.com")

    # Mock assíncrono da função send_email
    async def mock_send_email(title: str, message: str) -> None:
        pass

    monkeypatch.setattr("src.app.workers.scheduler.get_settings", lambda: settings)
    monkeypatch.setattr("src.app.workers.scheduler.get_whatsapp_service", lambda: service)
    monkeypatch.setattr("src.app.workers.scheduler.send_email", mock_send_email)

    WHATSAPP_NOTIFICATION_COUNTER.labels(status="failure")._value.set(0)  # type: ignore[attr-defined]
    FALLBACK_NOTIFICATION_COUNTER.labels(status="sent")._value.set(0)  # type: ignore[attr-defined]

    await _notify_whatsapp("Resumo do dia")

    assert WHATSAPP_NOTIFICATION_COUNTER.labels(status="failure")._value.get() == 1  # type: ignore[attr-defined]
    assert FALLBACK_NOTIFICATION_COUNTER.labels(status="sent")._value.get() == 1  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_notify_whatsapp_no_service(monkeypatch) -> None:
    settings = Settings(whatsapp_notify_numbers="5511999999999")

    monkeypatch.setattr("src.app.workers.scheduler.get_settings", lambda: settings)
    monkeypatch.setattr("src.app.workers.scheduler.get_whatsapp_service", lambda: None)

    # Should not raise even sem serviço
    await _notify_whatsapp("Resumo do dia")
