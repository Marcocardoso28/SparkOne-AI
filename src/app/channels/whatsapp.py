"""Evolution API (WhatsApp) adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.models.schemas import Channel, ChannelMessage


class WhatsAppPayload(BaseModel):
    sender: str = Field(..., alias="from")
    message: str
    timestamp: datetime | None = None
    extra_data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, value: Any) -> datetime | None:  # pragma: no cover - pydantic hook
        if value is None or value == "":
            return None
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return value


class WhatsAppAdapter:
    channel_name = Channel.WHATSAPP.value

    async def normalize(self, payload: dict[str, Any]) -> ChannelMessage:
        data = WhatsAppPayload.model_validate(payload)
        return ChannelMessage(
            channel=Channel.WHATSAPP,
            sender=data.sender,
            content=data.message,
            created_at=data.timestamp or datetime.now(UTC),
            extra_data=data.extra_data,
        )


__all__ = ["WhatsAppAdapter"]
