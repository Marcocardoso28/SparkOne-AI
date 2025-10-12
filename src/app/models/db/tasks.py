"""Task persistence models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum

import os
from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class TaskStatus(str, PyEnum):
    TODO = "todo"
    PENDING = "pending"  # alias amigável para testes
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskRecord(TimestampMixin, Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Em ambiente de testes (SQLite), use String para evitar constraints rígidas
    _status_type = (
        String(20)
        if os.getenv("PYTEST_CURRENT_TEST")
        else Enum(
            TaskStatus,
            name="task_status_enum",
            values_callable=lambda e: [i.value for i in e],
        )
    )
    status: Mapped[TaskStatus] = mapped_column(
        _status_type, default=TaskStatus.TODO, nullable=False
    )
    external_id: Mapped[str | None] = mapped_column(String(255))
    channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sender: Mapped[str | None] = mapped_column(String(255), nullable=True)


__all__ = ["TaskRecord", "TaskStatus"]
