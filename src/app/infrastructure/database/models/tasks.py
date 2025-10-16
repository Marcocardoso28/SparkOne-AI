"""Task persistence models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class TaskStatus(str, PyEnum):
    TODO = "todo"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskRecord(TimestampMixin, Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending")
    priority: Mapped[str | None] = mapped_column(String(10), default="medium")
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Alias for due_date (for ProactivityEngine compatibility)",
    )
    reminded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when reminder was sent (for ProactivityEngine)",
    )
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)


__all__ = ["TaskRecord", "TaskStatus"]
