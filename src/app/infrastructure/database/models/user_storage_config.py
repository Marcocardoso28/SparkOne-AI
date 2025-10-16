"""User storage configuration model."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class UserStorageConfig(TimestampMixin, Base):
    """User storage adapter configuration.

    Stores configuration for storage backends (Notion, ClickUp, Sheets, etc).
    Each user can have multiple configurations with different priorities.
    """

    __tablename__ = "user_storage_configs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default="gen_random_uuid()",
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="NULL for single-user mode, UUID for multi-tenant",
    )
    adapter_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Adapter type: notion, clickup, sheets",
    )
    config_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Adapter-specific configuration (api_key, database_id, etc)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Whether this config is active",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        comment="Sync priority (higher = first)",
    )


__all__ = ["UserStorageConfig"]
