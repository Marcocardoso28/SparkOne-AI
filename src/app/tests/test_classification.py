import pytest

from src.app.models.schemas import Channel, ChannelMessage, MessageType
from src.app.services.classification import ClassificationService


@pytest.mark.parametrize(
    "content,expected",
    [
        ("Preciso de um evento amanhã", MessageType.EVENT),
        ("Criar tarefa importante", MessageType.TASK),
        ("Por favor corrija este texto", MessageType.COACHING),
        ("Mensagem livre", MessageType.UNKNOWN),
    ],
)
@pytest.mark.asyncio
async def test_classification_service_heuristics(content: str, expected: MessageType) -> None:
    service = ClassificationService()
    payload = ChannelMessage(channel=Channel.WHATSAPP, sender="user", content=content)

    result = await service.classify(payload)

    assert result == expected
