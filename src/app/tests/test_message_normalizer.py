import pytest

from app.channels import (
    ChannelNotRegisteredError,
    GoogleSheetsAdapter,
    MessageNormalizer,
    WebUIAdapter,
    WhatsAppAdapter,
)
from app.models.schemas import Channel


@pytest.mark.asyncio
async def test_whatsapp_normalizer_parses_payload() -> None:
    normalizer = MessageNormalizer([WhatsAppAdapter(), GoogleSheetsAdapter(), WebUIAdapter()])
    payload = {"from": "551199999", "message": "Olá SparkOne"}

    message = await normalizer.normalize("whatsapp", payload)

    assert message.channel == Channel.WHATSAPP
    assert message.sender == "551199999"
    assert message.content == "Olá SparkOne"


@pytest.mark.asyncio
async def test_unknown_channel_raises() -> None:
    normalizer = MessageNormalizer([WhatsAppAdapter()])

    with pytest.raises(ChannelNotRegisteredError):
        await normalizer.normalize("email", {})
