"""Conversation memory models."""

from __future__ import annotations

from enum import Enum as PyEnum

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class ConversationRole(str, PyEnum):
    USER = "user"
    ASSISTANT = "assistant"


class ConversationMessage(TimestampMixin, Base):
    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[ConversationRole] = mapped_column(Enum(ConversationRole), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)


__all__ = ["ConversationMessage", "ConversationRole"]
