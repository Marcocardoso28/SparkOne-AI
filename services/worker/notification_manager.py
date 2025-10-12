"""Notification helpers used by the worker pipeline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

import structlog
from prometheus_client import Counter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings, get_settings
from app.core.database import get_session_factory
from app.dependencies import get_whatsapp_service
from app.services.email import send_email

logger = structlog.get_logger(__name__)

DELIVERY_COUNTER = Counter(
    "sparkone_worker_delivery_total",
    "Notification delivery attempts by channel and status",
    labelnames=["channel", "status"],
)

DLQ_REQUEUE_COUNTER = Counter(
    "sparkone_worker_dlq_requeues_total",
    "DLQ reprocessing outcomes",
    labelnames=["channel", "status"],
)

EmailSender = Callable[[str, str], Awaitable[None]]


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
        whatsapp_service: Any | None = None,
        email_sender: EmailSender | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._session_factory = session_factory or get_session_factory()
        self._settings = settings or get_settings()
        self._whatsapp_service = whatsapp_service or get_whatsapp_service()
        self._email_sender = email_sender or send_email

        numbers_raw = self._settings.whatsapp_notify_numbers or ""
        self._whatsapp_numbers = [num.strip() for num in numbers_raw.split(",") if num.strip()]
        self._email_recipient = self._settings.fallback_email

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
    ) -> dict[str, Any]:
        """Dispatch alert to configured channels and queue failures."""

        metadata = metadata or {}
        subject = self._compose_subject(job_name, severity)
        body = self._compose_body(job_name, severity, message, metadata)
        deliveries: list[dict[str, Any]] = []

        for number in self._whatsapp_numbers:
            deliveries.append(
                await self._deliver(
                    channel="whatsapp",
                    recipient=number,
                    job_name=job_name,
                    severity=severity,
                    subject=subject,
                    body=body,
                    metadata=metadata,
                )
            )

        if self._email_recipient:
            deliveries.append(
                await self._deliver(
                    channel="email",
                    recipient=self._email_recipient,
                    job_name=job_name,
                    severity=severity,
                    subject=subject,
                    body=body,
                    metadata=metadata,
                )
            )

        sent = sum(1 for item in deliveries if item["status"] == "sent")
        queued = sum(1 for item in deliveries if item["status"] == "queued")

        logger.info(
            "worker_alert_dispatched",
            job_name=job_name,
            severity=severity,
            message=message,
            metadata=metadata,
            delivered=sent,
            queued=queued,
            body_preview=body[:200],
        )

        return {"sent": sent, "queued": queued, "deliveries": deliveries}

    async def reprocess_dlq(self, *, limit: int = 20) -> dict[str, int]:
        """Attempt to redeliver queued notifications from the DLQ."""

        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT id, job_name, payload, retry_count
                    FROM worker_dlq
                    WHERE processed_at IS NULL
                    ORDER BY created_at ASC
                    LIMIT :limit
                    """
                ),
                {"limit": limit},
            )
            rows = result.mappings().all()

            success = 0
            failure = 0

            for row in rows:
                payload_data = json.loads(row["payload"] or "{}")
                channel = payload_data.get("channel") or "unknown"
                recipient = payload_data.get("recipient") or "unknown"
                severity = payload_data.get("severity", "info")
                metadata = payload_data.get("metadata") or {}
                body = payload_data.get("body") or payload_data.get("message") or ""
                subject = payload_data.get("subject") or self._compose_subject(row["job_name"], severity)

                try:
                    await self._attempt_send(
                        channel=channel,
                        recipient=recipient,
                        subject=subject,
                        body=body,
                    )
                except Exception as exc:  # pragma: no cover - defensive guard
                    failure += 1
                    DELIVERY_COUNTER.labels(channel=channel, status="failure").inc()
                    DLQ_REQUEUE_COUNTER.labels(channel=channel, status="failure").inc()
                    await session.execute(
                        text(
                            """
                            UPDATE worker_dlq
                            SET retry_count = retry_count + 1,
                                error_message = :error_message
                            WHERE id = :entry_id
                            """
                        ),
                        {
                            "error_message": str(exc),
                            "entry_id": row["id"],
                        },
                    )
                    continue

                success += 1
                DELIVERY_COUNTER.labels(channel=channel, status="success").inc()
                DLQ_REQUEUE_COUNTER.labels(channel=channel, status="success").inc()
                await session.execute(
                    text(
                        """
                        UPDATE worker_dlq
                        SET processed_at = :processed_at,
                            retry_count = retry_count + 1,
                            error_message = ''
                        WHERE id = :entry_id
                        """
                    ),
                    {
                        "processed_at": datetime.now(timezone.utc),
                        "entry_id": row["id"],
                    },
                )

            await session.commit()

        logger.info(
            "worker_dlq_reprocess",
            attempted=len(rows),
            success=success,
            failure=failure,
        )

        return {"attempted": len(rows), "success": success, "failure": failure}

    async def _deliver(
        self,
        *,
        channel: str,
        recipient: str,
        job_name: str,
        severity: str,
        subject: str,
        body: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            await self._attempt_send(
                channel=channel,
                recipient=recipient,
                subject=subject,
                body=body,
            )
        except Exception as exc:  # pragma: no cover - handled in tests
            DELIVERY_COUNTER.labels(channel=channel, status="failure").inc()
            await self.enqueue_dlq(
                job_name=job_name,
                payload={
                    "channel": channel,
                    "recipient": recipient,
                    "severity": severity,
                    "message": body,
                    "metadata": metadata,
                    "subject": subject,
                },
                error=str(exc),
                scheduled_for=None,
            )
            return {"channel": channel, "recipient": recipient, "status": "queued", "error": str(exc)}

        DELIVERY_COUNTER.labels(channel=channel, status="success").inc()
        return {"channel": channel, "recipient": recipient, "status": "sent"}

    async def _attempt_send(
        self,
        *,
        channel: str,
        recipient: str,
        subject: str,
        body: str,
    ) -> None:
        if channel == "whatsapp":
            if self._whatsapp_service is None:
                raise RuntimeError("whatsapp service not configured")
            await self._whatsapp_service.send_text(recipient, body)
            return

        if channel == "email":
            await self._email_sender(subject, body)
            return

        raise ValueError(f"unsupported channel: {channel}")

    def _compose_subject(self, job_name: str, severity: str) -> str:
        return f"SparkOne Worker [{severity.upper()}] {job_name}"

    def _compose_body(
        self,
        job_name: str,
        severity: str,
        message: str,
        metadata: dict[str, Any],
    ) -> str:
        details = json.dumps(metadata, indent=2, default=_json_default) if metadata else "(sem detalhes)"
        return (
            f"Job: {job_name}\n"
            f"Severidade: {severity}\n"
            f"Mensagem: {message}\n\n"
            f"Detalhes:\n{details}"
        )


__all__ = ["NotificationManager", "DELIVERY_COUNTER", "DLQ_REQUEUE_COUNTER"]
