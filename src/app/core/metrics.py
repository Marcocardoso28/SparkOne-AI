"""Prometheus metrics instrumentation."""

from __future__ import annotations

from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "sparkone_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "sparkone_http_request_latency_seconds",
    "Latency of HTTP requests",
    ["method", "endpoint"],
    buckets=(0.05, 0.1, 0.3, 0.5, 1, 2, 5),
)

NOTION_SYNC_COUNTER = Counter(
    "sparkone_notion_sync_total",
    "Notion synchronization attempts",
    ["status"],
)

INGESTION_COUNTER = Counter(
    "sparkone_ingestion_total",
    "Status of message ingestion pipeline",
    ["status"],
)

CLASSIFICATION_COUNTER = Counter(
    "sparkone_classification_total",
    "Classification decisions emitted by the orchestrator",
    ["result"],
)

SHEETS_SYNC_COUNTER = Counter(
    "sparkone_sheets_sync_total",
    "Google Sheets synchronization results",
    ["status"],
)

WHATSAPP_NOTIFICATION_COUNTER = Counter(
    "sparkone_whatsapp_notifications_total",
    "WhatsApp notifications attempts",
    ["status"],
)

FALLBACK_NOTIFICATION_COUNTER = Counter(
    "sparkone_fallback_notifications_total",
    "Fallback notification attempts",
    ["status"],
)


__all__ = [
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "NOTION_SYNC_COUNTER",
    "INGESTION_COUNTER",
    "CLASSIFICATION_COUNTER",
    "SHEETS_SYNC_COUNTER",
    "WHATSAPP_NOTIFICATION_COUNTER",
    "FALLBACK_NOTIFICATION_COUNTER",
]
