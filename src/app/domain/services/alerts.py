"""Forwarding of alert events (e.g., from Prometheus Alertmanager) to WhatsApp."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from pydantic import BaseModel

from app.config import get_settings
from app.core.metrics import FALLBACK_NOTIFICATION_COUNTER, WHATSAPP_NOTIFICATION_COUNTER
from app.api.dependencies import get_whatsapp_service


class Alert(BaseModel):
    status: str
    labels: dict[str, str]
    annotations: dict[str, str]


class AlertPayload(BaseModel):
    alerts: Sequence[Alert]


async def forward_alerts_to_whatsapp(payload: AlertPayload) -> None:
    settings = get_settings()
    numbers_raw = settings.whatsapp_notify_numbers
    if not numbers_raw:
        return

    service = get_whatsapp_service()
    if service is None:
        await _fallback_notification(payload)
        return

    numbers = [n.strip() for n in numbers_raw.split(",") if n.strip()]
    for alert in payload.alerts:
        message = _format_alert(alert)
        for number in numbers:
            try:
                await service.send_text(number, message)
                WHATSAPP_NOTIFICATION_COUNTER.labels(status="success").inc()
            except Exception:  # pragma: no cover - external failure path
                WHATSAPP_NOTIFICATION_COUNTER.labels(status="failure").inc()
                await _fallback_notification(AlertPayload(alerts=[alert]))


async def _fallback_notification(payload: AlertPayload) -> None:
    settings = get_settings()
    if not settings.fallback_email:
        return
    FALLBACK_NOTIFICATION_COUNTER.labels(status="sent").inc()
    logging.getLogger(__name__).info(
        "fallback_alert", email=settings.fallback_email, alerts=len(payload.alerts)
    )


def _format_alert(alert: Alert) -> str:
    summary = alert.annotations.get("summary", "Alerta SparkOne")
    description = alert.annotations.get("description", "")
    severity = alert.labels.get("severity", "info").upper()
    return f"[{severity}] {summary}\n{description}"


__all__ = ["Alert", "AlertPayload", "forward_alerts_to_whatsapp"]
