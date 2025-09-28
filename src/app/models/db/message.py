"""ORM models for channel messages."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.schemas import Channel, MessageType

from .base import Base, TimestampMixin


class ChannelMessageORM(TimestampMixin, Base):
    """Normalized message stored after ingestion."""

    __tablename__ = "channel_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel: Mapped[Channel] = mapped_column(Enum(Channel), nullable=False)
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    message_type: Mapped[MessageType] = mapped_column(Enum(MessageType), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(nullable=False)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)


__all__ = ["ChannelMessageORM"]
