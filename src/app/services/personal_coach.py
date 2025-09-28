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
        """Provide coaching and personal development guidance."""

        coaching_prompt = (
            "Você é um coach pessoal especializado em desenvolvimento, produtividade e motivação. "
            "O usuário está pedindo conselhos ou orientação. Forneça uma resposta útil, motivadora e prática. "
            "Seja empático, positivo e ofereça dicas acionáveis.\n\n"
            f"Pergunta/pedido do usuário: {payload.content}\n\n"
            "Forneça uma resposta de coaching útil e motivadora:"
        )

        try:
            response = await self._chat.generate(
                messages=[
                    {"role": "system", "content": DEFAULT_PERSONA_PROMPT},
                    {"role": "user", "content": coaching_prompt},
                ],
                temperature=0.7,
                task_type="smart",  # Usar modelo inteligente para coaching
            )
            return {
                "status": "responded",
                "response": response,
                "category": "coaching"
            }
        except Exception:
            return {
                "status": "error",
                "response": "Desculpe, não consegui gerar uma resposta de coaching no momento. Tente novamente.",
                "category": "coaching"
            }


__all__ = ["PersonalCoachService"]
