"""Services responsible for message classification."""

from __future__ import annotations

import structlog

from ..agents.agno import AgnoBridge
from ..core.metrics import CLASSIFICATION_COUNTER
from ..models.schemas import ChannelMessage, MessageType

logger = structlog.get_logger(__name__)


class ClassificationService:
    """Heurística com fallback ao AgnoBridge."""

    def __init__(self, agno: AgnoBridge | None = None) -> None:
        self._agno = agno

    async def classify(self, payload: ChannelMessage) -> MessageType:
        if payload.message_type != MessageType.FREE_TEXT:
            result = payload.message_type
        else:
            text = payload.content.lower()
            if any(keyword in text for keyword in ("agenda", "evento", "calendário")):
                result = MessageType.EVENT
            elif any(keyword in text for keyword in ("tarefa", "a fazer", "task")):
                result = MessageType.TASK
            elif any(keyword in text for keyword in ("corrija", "melhore", "corre\u00e7\u00e3o")):
                result = MessageType.COACHING
            elif self._agno is not None:
                try:
                    result, _ = await self._agno.classify(payload)
                except Exception as exc:  # pragma: no cover - LLM failure path
                    logger.warning("classification_agno_failed", error=str(exc))
                    result = MessageType.UNKNOWN
            else:
                result = MessageType.UNKNOWN

        CLASSIFICATION_COUNTER.labels(result=result.value).inc()
        return result


__all__ = ["ClassificationService"]
