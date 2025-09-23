"""High-level orchestrator coordinating channel messages."""

from __future__ import annotations

from typing import Any

from ..models.schemas import ChannelMessage, MessageType
from ..services.calendar import CalendarService
from ..services.classification import ClassificationService
from ..services.personal_coach import PersonalCoachService
from ..services.tasks import TaskService
from .agno import AgnoBridge


class Orchestrator:
    """Routes messages to the appropriate domain services."""

    def __init__(
        self,
        classification: ClassificationService,
        task_service: TaskService,
        calendar_service: CalendarService,
        coach_service: PersonalCoachService,
        agno_bridge: AgnoBridge | None = None,
    ) -> None:
        self._classification = classification
        self._task_service = task_service
        self._calendar_service = calendar_service
        self._coach_service = coach_service
        self._agno = agno_bridge

    async def handle(self, payload: ChannelMessage) -> dict[str, Any]:
        """Classify the payload and invoke the matching handler."""

        message_type = await self._classification.classify(payload)
        if message_type == MessageType.TASK:
            return await self._task_service.handle(payload)
        if message_type == MessageType.EVENT:
            return await self._calendar_service.handle(payload)
        if message_type == MessageType.COACHING:
            return await self._coach_service.handle(payload)
        if self._agno is not None:
            category, summary = await self._agno.classify(payload)
            response = await self._agno.respond(category=category, summary=summary)
            return {
                "status": "responded",
                "category": category.value,
                "summary": summary,
                "response": response,
            }
        return {"status": "queued", "details": "Unhandled message type"}


__all__ = ["Orchestrator"]
