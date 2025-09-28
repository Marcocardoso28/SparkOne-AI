"""Short-term conversation memory service."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.memory import ConversationRole
from app.models.db.repositories import append_conversation_message, list_recent_conversations
from app.models.schemas import ChannelMessage


class MemoryService:
    """Handles user/assistant message buffering for personalization."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def store_user_message(self, payload: ChannelMessage) -> None:
        await append_conversation_message(
            self._session,
            conversation_id=f"{payload.channel.value}_{payload.sender}",
            channel=payload.channel.value,
            sender=payload.sender,
            role=ConversationRole.USER,
            content=payload.content,
        )

    async def store_assistant_message(self, *, channel: str, content: str) -> None:
        await append_conversation_message(
            self._session,
            conversation_id=f"{channel}_sparkone",
            channel=channel,
            sender="sparkone",
            role=ConversationRole.ASSISTANT,
            content=content,
        )

    async def recent_messages(self, limit: int = 10):
        return await list_recent_conversations(self._session, limit=limit)


__all__ = ["MemoryService"]
