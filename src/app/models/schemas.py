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
    sender: str = Field(...,
                        description="Identifier of the message originator")
    content: str = Field(..., description="Plain text message content")
    message_type: MessageType = MessageType.FREE_TEXT
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    extra_data: dict[str, Any] = Field(default_factory=dict)


class HealthStatus(BaseModel):
    """Response model for health checks."""

    status: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="development",
                             description="Environment name")


class DatabaseHealthStatus(BaseModel):
    """Response model for database health checks."""

    status: str
    database: str = Field(default="sqlite", description="Database type")
    connected: bool = Field(
        default=True, description="Database connection status")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RedisHealthStatus(BaseModel):
    """Response model for Redis health checks."""

    status: str
    redis: str = Field(default="redis", description="Redis service name")
    connected: bool = Field(
        default=True, description="Redis connection status")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


__all__ = ["Channel", "ChannelMessage", "HealthStatus",
           "DatabaseHealthStatus", "RedisHealthStatus", "MessageType"]
