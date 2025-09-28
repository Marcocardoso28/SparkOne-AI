"""Google Sheets adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.schemas import Channel, ChannelMessage, MessageType


class GoogleSheetsPayload(BaseModel):
    row: list[str]
    sheet_id: str
    user: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    row_index: int | None = None


class GoogleSheetsAdapter:
    channel_name = Channel.GOOGLE_SHEETS.value

    async def normalize(self, payload: dict[str, Any]) -> ChannelMessage:
        data = GoogleSheetsPayload.model_validate(payload)
        content = "\n".join(data.row)
        extra_data = {
            "sheet_id": data.sheet_id,
            "row_length": len(data.row),
            "row_index": data.row_index,
        }
        return ChannelMessage(
            channel=Channel.GOOGLE_SHEETS,
            sender=data.user,
            content=content,
            message_type=MessageType.FREE_TEXT,
            created_at=data.timestamp,
            extra_data=extra_data,
        )


__all__ = ["GoogleSheetsAdapter"]
