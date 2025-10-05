"""Event monitor helpers for the worker service."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_session_factory

logger = structlog.get_logger(__name__)


def _iso_or_none(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):  # pragma: no cover - helper guard
        return value.isoformat()
    return str(value)


class EventMonitor:
    """Persist scheduler events and emit structured logs."""

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self._session_factory = session_factory or get_session_factory()

    async def record_job_event(
        self,
        *,
        job_name: str,
        status: str,
        runtime_seconds: float,
        started_at: datetime,
        finished_at: datetime,
        scheduled_for: datetime | None,
        payload: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        payload_json = json.dumps(payload or {}, default=_json_default)
        async with self._session_factory() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO worker_job_events (
                        job_name,
                        status,
                        scheduled_at,
                        started_at,
                        finished_at,
                        runtime_seconds,
                        payload,
                        error_message
                    )
                    VALUES (:job_name, :status, :scheduled_at, :started_at, :finished_at, :runtime_seconds, :payload, :error_message)
                    """
                ),
                {
                    "job_name": job_name,
                    "status": status,
                    "scheduled_at": scheduled_for,
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "runtime_seconds": runtime_seconds,
                    "payload": payload_json,
                    "error_message": error,
                },
            )
            await session.commit()

        logger.info(
            "worker_job_event",
            job_name=job_name,
            status=status,
            runtime_seconds=runtime_seconds,
            scheduled_at=_iso_or_none(scheduled_for),
            started_at=_iso_or_none(started_at),
            finished_at=_iso_or_none(finished_at),
            error=error,
            payload_preview=payload_json[:200],
        )


__all__ = ["EventMonitor"]
