"""Personal coach service for text corrections and suggestions."""

from __future__ import annotations

from typing import Any

from app.models.schemas import ChannelMessage
from app.providers.chat import ChatProviderRouter
from app.settings.persona import DEFAULT_PERSONA_PROMPT


class PersonalCoachService:
    """Leverages LLM providers to improve user texts and suggestions."""

    def __init__(self, chat_provider: ChatProviderRouter) -> None:
        self._chat = chat_provider

    async def handle(self, payload: ChannelMessage) -> dict[str, Any]:
        """Return a placeholder response until the LLM prompt is finalized."""

        # TODO: craft full prompt and parse structured response.
        message = (
            f"{DEFAULT_PERSONA_PROMPT}\n\n"
            f"Texto enviado: {payload.content}\n"
            "Resposta padrão: recurso de coaching em desenvolvimento."
        )
        return {"status": "pending", "message": message}


__all__ = ["PersonalCoachService"]
