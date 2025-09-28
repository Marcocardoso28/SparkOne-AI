"""Domain service for task management."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.metrics import NOTION_SYNC_COUNTER
from app.integrations.notion import NotionClient
from app.models.db.repositories import create_task
from app.models.db.tasks import TaskStatus
from app.models.schemas import ChannelMessage

logger = structlog.get_logger(__name__)


class TaskService:
    """Handles synchronization of tasks with Notion and local storage."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        notion_client: NotionClient | None = None,
        notion_database_id: str | None = None,
    ) -> None:
        self._session = session
        self._notion = notion_client
        self._database_id = notion_database_id

    async def handle(self, payload: ChannelMessage) -> dict[str, Any]:
        """Persist tarefa localmente e replica opcionalmente para o Notion."""

        due_at = self._parse_due_date(payload.extra_data.get("due_at"))
        description = payload.extra_data.get("description")
        record = await create_task(
            self._session,
            title=payload.content[:255],
            description=description,
            due_at=due_at,
            channel=payload.channel.value,
            sender=payload.sender,
            status=TaskStatus.TODO,
        )

        notion_id: str | None = None
        if self._notion and self._database_id:
            try:
                notion_payload = self._build_notion_payload(record.title, description, due_at)
                notion_payload["parent"] = {"database_id": self._database_id}
                response = await self._notion.create_page(notion_payload)
                notion_id = response.get("id") if isinstance(response, dict) else None
                NOTION_SYNC_COUNTER.labels(status="success").inc()
            except Exception as exc:  # pragma: no cover - external failure path
                logger.warning("notion_sync_failed", error=str(exc))
                NOTION_SYNC_COUNTER.labels(status="failure").inc()

        if notion_id:
            record.external_id = notion_id
            self._session.add(record)

        return {
            "status": "created",
            "task_id": record.id,
            "notion_id": notion_id,
            "due_at": due_at.isoformat() if due_at else None,
            "response": f"Tarefa criada com sucesso: '{payload.content[:100]}{'...' if len(payload.content) > 100 else ''}'. " +
                       (f"Prazo: {due_at.strftime('%d/%m/%Y às %H:%M')}" if due_at else "Sem prazo definido."),
        }

    def _parse_due_date(self, value: Any) -> datetime | None:  # pragma: no cover - simple helper
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return None

    def _build_notion_payload(
        self,
        title: str,
        description: str | None,
        due_at: datetime | None,
    ) -> dict[str, Any]:
        properties: dict[str, Any] = {
            "Name": {
                "title": [
                    {
                        "text": {"content": title},
                    }
                ]
            }
        }
        if due_at:
            properties["Due"] = {"date": {"start": due_at.isoformat()}}
        if description:
            properties["Description"] = {"rich_text": [{"text": {"content": description[:2000]}}]}

        return {"properties": properties}


__all__ = ["TaskService"]
