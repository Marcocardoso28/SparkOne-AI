"""Bridge to simulate Agno orchestrator interactions."""

from __future__ import annotations

import structlog

from app.models.schemas import ChannelMessage, MessageType
from app.providers.chat import ChatProviderRouter, LLMGenerationError
from .prompts.orchestrator import CLASSIFICATION_PROMPT, RESPONSE_PROMPT, SYSTEM_PROMPT
from .tools.parser import safe_json_loads


class AgnoBridge:
    """Lightweight orchestrator using LLM to emulate Agno behaviour."""

    def __init__(self, chat_provider: ChatProviderRouter) -> None:
        self._chat = chat_provider
        self._logger = structlog.get_logger(__name__)

    async def classify(self, payload: ChannelMessage) -> tuple[MessageType, str]:
        prompt = CLASSIFICATION_PROMPT.format(message=payload.content)
        try:
            response = await self._chat.generate(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
        except LLMGenerationError as exc:
            self._logger.warning("agno_classification_failed", error=str(exc))
            return MessageType.UNKNOWN, ""
        data = safe_json_loads(response)
        category = data.get("category", "OUTRO").upper()
        summary = data.get("summary", "")
        try:
            return MessageType[category], summary
        except KeyError:
            return MessageType.UNKNOWN, summary

    async def respond(self, *, category: MessageType, summary: str) -> str:
        prompt = RESPONSE_PROMPT.format(category=category.value, summary=summary)
        try:
            response = await self._chat.generate(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
        except LLMGenerationError as exc:
            self._logger.warning("agno_response_failed", error=str(exc), category=category.value)
            return "Não consegui gerar uma resposta no momento."
        return response


__all__ = ["AgnoBridge"]
