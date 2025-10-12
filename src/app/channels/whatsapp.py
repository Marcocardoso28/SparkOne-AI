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
        if isinstance(value, int | float):
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
        """Normalize payloads from Evolution API or direct minimal format.

        Accepted shapes:
        - Minimal: {"from": "5511...", "message": "...", "timestamp": ...}
        - Evolution webhook: {"data": {"key": {"remoteJid": "...@s.whatsapp.net", "id": "..."},
          "message": {"conversation": "..."}, "messageTimestamp": 1700000000}}
        """

        # Try minimal format first
        try:
            data = WhatsAppPayload.model_validate(payload)
            return ChannelMessage(
                channel=Channel.WHATSAPP,
                sender=data.sender,
                content=data.message,
                created_at=data.timestamp or datetime.now(UTC),
                extra_data=data.extra_data,
            )
        except Exception:
            pass

        # Try Evolution API webhook format
        try:
            evo = payload.get("data", {}) if isinstance(payload, dict) else {}
            key = evo.get("key", {})
            remote_jid = key.get("remoteJid") or ""
            # Extract phone from remoteJid if present
            sender = remote_jid.split("@")[0] if remote_jid else "unknown"
            message_obj = evo.get("message", {})
            content = message_obj.get("conversation") or ""
            timestamp = evo.get("messageTimestamp")
            external_id = key.get("id")

            ts = None
            if isinstance(timestamp, (int, float)):
                ts = datetime.fromtimestamp(timestamp, tz=UTC)

            extra: dict[str, Any] = {"raw": "evolution"}
            if external_id:
                extra["external_id"] = external_id

            return ChannelMessage(
                channel=Channel.WHATSAPP,
                sender=sender,
                content=content,
                created_at=ts or datetime.now(UTC),
                extra_data=extra,
                external_id=external_id,
            )
        except Exception as exc:  # pragma: no cover - fallback
            raise ValueError(f"Invalid WhatsApp payload: {exc}")


__all__ = ["WhatsAppAdapter"]
