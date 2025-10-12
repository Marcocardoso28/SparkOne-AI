"""Pydantic data models shared across the API."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Channel(str, Enum):
    """Supported ingestion channels."""

    WHATSAPP = "whatsapp"
    GOOGLE_SHEETS = "google_sheets"
    WEB = "web"


class MessageType(str, Enum):
    """High-level message classification expected by the orchestrator."""

    FREE_TEXT = "free_text"
    TASK = "task"
    EVENT = "event"
    COACHING = "coaching"
    UNKNOWN = "unknown"


class ChannelMessage(BaseModel):
    """Normalized payload produced by ingestion adapters."""

    channel: Channel
    sender: str = Field(..., description="Identifier of the message originator")
    content: str = Field(..., description="Plain text message content")
    message_type: MessageType = MessageType.FREE_TEXT
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    extra_data: dict[str, Any] = Field(default_factory=dict)
    external_id: str | None = None


class HealthStatus(BaseModel):
    """Response model for health checks."""

    status: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


__all__ = ["Channel", "ChannelMessage", "HealthStatus", "MessageType"]
