"""Domain service for task management."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.metrics import NOTION_SYNC_COUNTER
from app.infrastructure.database.models.repositories import create_task
from app.infrastructure.database.models.tasks import TaskStatus
from app.models.schemas import ChannelMessage
from app.domain.services.storage import StorageService

logger = structlog.get_logger(__name__)


class TaskService:
    """Handles synchronization of tasks with multiple storage backends.

    Now uses StorageService for multi-backend support (Notion, ClickUp, Sheets).
    Maintains backward compatibility with legacy Notion-only code.
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        storage_service: StorageService | None = None,
        user_id: str | None = None,
    ) -> None:
        """Initialize task service.

        Args:
            session: Database session
            storage_service: Optional StorageService instance (if None, legacy mode)
            user_id: User ID for loading storage configs (None = single-user mode)
        """
        self._session = session
        self._storage_service = storage_service
        self._user_id = user_id
        self._storage_loaded = False

    async def handle(self, payload: ChannelMessage) -> dict[str, Any]:
        """Persist task locally and optionally replicate to storage backends.

        Now supports multi-backend sync via StorageService.
        Maintains backward compatibility with legacy Notion-only mode.
        """

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

        # Multi-backend sync via StorageService
        external_ids: dict[str, str] = {}
        if self._storage_service:
            try:
                # Load storage configs if not already loaded
                if not self._storage_loaded:
                    await self._storage_service.load_configs(user_id=self._user_id)
                    self._storage_loaded = True

                # Save to all active backends in parallel
                external_ids = await self._storage_service.save_task(record)

                # Update metrics for each backend
                for adapter_name in external_ids:
                    if adapter_name == "notion":
                        NOTION_SYNC_COUNTER.labels(status="success").inc()

                # Store primary external_id (first successful backend)
                if external_ids:
                    # Prefer notion for backward compatibility, else use first result
                    primary_id = external_ids.get("notion") or next(iter(external_ids.values()))
                    record.external_id = primary_id
                    self._session.add(record)

            except Exception as exc:  # pragma: no cover - external failure path
                logger.warning("storage_sync_failed", error=str(exc))
                NOTION_SYNC_COUNTER.labels(status="failure").inc()

        return {
            "status": "created",
            "task_id": record.id,
            "external_ids": external_ids,  # All backend IDs
            "notion_id": external_ids.get("notion"),  # Backward compatibility
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


__all__ = ["TaskService"]
