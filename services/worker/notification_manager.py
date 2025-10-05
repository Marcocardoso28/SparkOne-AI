"""Notification helpers used by the worker pipeline."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_session_factory

logger = structlog.get_logger(__name__)


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):  # pragma: no cover - helper guard
        return value.isoformat()
    return str(value)


def _iso_or_none(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


class NotificationManager:
    """Persist failed workloads into the DLQ and emit alert logs."""

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self._session_factory = session_factory or get_session_factory()

    async def enqueue_dlq(
        self,
        *,
        job_name: str,
        payload: dict[str, Any] | None,
        error: str,
        scheduled_for: datetime | None,
        retry_count: int = 0,
    ) -> None:
        payload_json = json.dumps(payload or {}, default=_json_default)
        async with self._session_factory() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO worker_dlq (
                        job_name,
                        payload,
                        error_message,
                        scheduled_for,
                        retry_count
                    )
                    VALUES (:job_name, :payload, :error_message, :scheduled_for, :retry_count)
                    """
                ),
                {
                    "job_name": job_name,
                    "payload": payload_json,
                    "error_message": error,
                    "scheduled_for": scheduled_for,
                    "retry_count": retry_count,
                },
            )
            await session.commit()

        logger.warning(
            "worker_dlq_enqueued",
            job_name=job_name,
            retry_count=retry_count,
            scheduled_at=_iso_or_none(scheduled_for),
            error=error,
            payload_preview=payload_json[:200],
        )

    async def send_alert(
        self,
        *,
        job_name: str,
        severity: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Stub alert dispatcher that just emits a structured log entry."""

        logger.info(
            "worker_alert_dispatched",
            job_name=job_name,
            severity=severity,
            message=message,
            metadata=metadata or {},
        )


__all__ = ["NotificationManager"]
