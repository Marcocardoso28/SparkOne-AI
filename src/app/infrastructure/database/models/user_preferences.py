"""User preferences model for ProactivityEngine configuration.

Stores user-specific settings for notifications, brief times, and reminders.

Related to: ADR-015 (User Preferences System), RF-020
"""

from __future__ import annotations

from datetime import time
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Integer, String, Time
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class UserPreferences(TimestampMixin, Base):
    """User preferences for ProactivityEngine and notifications.

    Stores configuration for:
    - Daily brief time (customizable per user)
    - Timezone (IANA format, e.g., 'America/Sao_Paulo')
    - Notification channels (WhatsApp, email, etc)
    - Deadline reminder window (hours before due date)
    - Additional flexible preferences (JSONB)

    Example:
        ```python
        prefs = UserPreferences(
            user_id=None,  # Single-user mode
            brief_time=time(8, 0),
            timezone="America/Sao_Paulo",
            notification_channels=["whatsapp"],
            deadline_reminder_hours=24,
            preferences_json={"whatsapp_number": "+5511999999999"}
        )
        ```
    """

    __tablename__ = "user_preferences"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default="gen_random_uuid()",
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        unique=True,
        comment="NULL for single-user mode",
    )
    brief_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
        server_default="08:00:00",
        comment="Daily brief time (HH:MM:SS)",
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="America/Sao_Paulo",
        comment="User timezone (IANA format)",
    )
    notification_channels: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default='["whatsapp"]',
        comment="Enabled notification channels",
    )
    deadline_reminder_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="24",
        comment="Hours before deadline to send reminder",
    )
    preferences_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Additional user preferences (flexible schema)",
    )

    @property
    def whatsapp_number(self) -> str | None:
        """Get WhatsApp number from preferences_json.

        Returns:
            str | None: WhatsApp number or None if not configured
        """
        return self.preferences_json.get("whatsapp_number")

    @whatsapp_number.setter
    def whatsapp_number(self, value: str | None) -> None:
        """Set WhatsApp number in preferences_json.

        Args:
            value: WhatsApp number to store
        """
        self.preferences_json["whatsapp_number"] = value


__all__ = ["UserPreferences"]
