"""Brief generation service."""

from __future__ import annotations

from datetime import datetime, timezone

import structlog

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.db.events import EventRecord, EventStatus
from ..models.db.tasks import TaskRecord, TaskStatus
from ..models.db.memory import ConversationMessage, ConversationRole
from ..providers.chat import ChatProviderRouter, LLMGenerationError


class BriefService:
    """Aggregates state from tasks, events and recent conversations."""

    def __init__(self, session: AsyncSession, chat_provider: ChatProviderRouter | None = None) -> None:
        self._session = session
        self._chat_provider = chat_provider if chat_provider and chat_provider.available else None
        self._logger = structlog.get_logger(__name__)

    async def structured_brief(self) -> dict:
        tasks = await self._pending_tasks()
        events = await self._upcoming_events()
        conversations = await self._recent_conversations()
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tasks": tasks,
            "events": events,
            "conversations": conversations,
        }

    async def textual_brief(self) -> str:
        data = await self.structured_brief()
        if self._chat_provider is None:
            return self._fallback_text(data)
        prompt = (
            "Monte um brief curto com base nos dados a seguir, abordando tarefas pendentes, "
            "eventos futuros e pontos de conversa recentes.\n\n"
            f"Dados: {data}"
        )
        try:
            response = await self._chat_provider.generate(
                messages=[
                    {"role": "system", "content": "Você é SparkOne, assistente pessoal do Marco."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
        except LLMGenerationError as exc:  # pragma: no cover - LLM failure path
            self._logger.warning("brief_generation_failed", error=str(exc))
            return self._fallback_text(data)
        return response

    async def _pending_tasks(self) -> list[dict]:
        stmt = select(TaskRecord).where(TaskRecord.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])).order_by(TaskRecord.due_at.nulls_last(), TaskRecord.id.desc()).limit(20)
        result = await self._session.execute(stmt)
        tasks: list[dict] = []
        for row in result.scalars():
            tasks.append(
                {
                    "id": row.id,
                    "title": row.title,
                    "status": row.status.value,
                    "due_at": row.due_at.isoformat() if row.due_at else None,
                }
            )
        return tasks

    async def _upcoming_events(self) -> list[dict]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(EventRecord)
            .where(EventRecord.start_at >= now)
            .order_by(EventRecord.start_at.asc())
            .limit(20)
        )
        result = await self._session.execute(stmt)
        events: list[dict] = []
        for row in result.scalars():
            events.append(
                {
                    "id": row.id,
                    "title": row.title,
                    "start_at": row.start_at.isoformat(),
                    "status": row.status.value,
                }
            )
        return events

    async def _recent_conversations(self) -> list[dict]:
        stmt = (
            select(ConversationMessage)
            .order_by(ConversationMessage.id.desc())
            .limit(10)
        )
        result = await self._session.execute(stmt)
        messages: list[dict] = []
        for row in result.scalars():
            messages.append(
                {
                    "role": row.role.value,
                    "content": row.content,
                    "channel": row.channel,
                    "timestamp": row.created_at.isoformat(),
                }
            )
        return list(reversed(messages))

    def _fallback_text(self, data: dict) -> str:
        parts: list[str] = ["Resumo SparkOne"]
        if data["tasks"]:
            tasks = "; ".join(f"#{item['id']} {item['title']} (status: {item['status']})" for item in data["tasks"][:5])
            parts.append(f"Tarefas pendentes: {tasks}.")
        if data["events"]:
            events = "; ".join(f"{item['title']} em {item['start_at']}" for item in data["events"][:5])
            parts.append(f"Próximos eventos: {events}.")
        if data["conversations"]:
            parts.append("Últimas conversas registradas.")
        return " \n".join(parts)


__all__ = ["BriefService"]
