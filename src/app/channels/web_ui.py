"""Web UI adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from ..models.schemas import Channel, ChannelMessage


class WebUIPayload(BaseModel):
    user_id: str
    content: str
    email: EmailStr | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    extra_data: dict[str, Any] = Field(default_factory=dict)


class WebUIAdapter:
    channel_name = Channel.WEB.value

    async def normalize(self, payload: dict[str, Any]) -> ChannelMessage:
        data = WebUIPayload.model_validate(payload)
        meta = {"email": data.email, **data.extra_data}
        return ChannelMessage(
            channel=Channel.WEB,
            sender=data.user_id,
            content=data.content,
            created_at=data.timestamp,
            extra_data=meta,
        )


__all__ = ["WebUIAdapter"]
