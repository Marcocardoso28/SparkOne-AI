from __future__ import annotations

import pytest

from app.services.whatsapp import WhatsAppService


class DummyClient:
    def __init__(self, fail_times: int = 0) -> None:
        self.fail_times = fail_times
        self.calls: int = 0

    async def send_message(self, payload):  # type: ignore[no-untyped-def]
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("network error")
        return {"status": "ok", "payload": payload}


@pytest.mark.asyncio
async def test_whatsapp_service_retries_and_succeeds() -> None:
    client = DummyClient(fail_times=2)
    service = WhatsAppService(client, max_retries=3)

    await service.send_text("+5511999999999", "Olá")

    assert client.calls == 3


@pytest.mark.asyncio
async def test_whatsapp_service_exhausts_retries() -> None:
    client = DummyClient(fail_times=5)
    service = WhatsAppService(client, max_retries=2)

    with pytest.raises(RuntimeError):
        await service.send_text("+5511999999999", "Olá")

    assert client.calls == 2
