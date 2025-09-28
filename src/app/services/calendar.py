"""Domain service for calendar integrations."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.caldav import CalDAVClient
from app.integrations.google_calendar import GoogleCalendarClient
from app.models.db.events import EventStatus
from app.models.db.repositories import create_event
from app.models.schemas import ChannelMessage

logger = structlog.get_logger(__name__)


class CalendarService:
    """Synchronizes events with selected calendar providers."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        caldav_client: CalDAVClient | None = None,
        google_client: GoogleCalendarClient | None = None,
        calendar_id: str | None = None,
        default_timezone: ZoneInfo | None = None,
    ) -> None:
        self._session = session
        self._caldav = caldav_client
        self._google = google_client
        self._calendar_id = calendar_id
        self._default_timezone = default_timezone or ZoneInfo("UTC")

    async def handle(self, payload: ChannelMessage) -> dict[str, Any]:
        """Create local event and push to provider if configured."""

        start_at = self._parse_datetime(payload.extra_data.get("start_at")) or datetime.now(
            self._default_timezone
        )
        end_at = self._parse_datetime(payload.extra_data.get("end_at"))
        location = payload.extra_data.get("location")
        description = payload.extra_data.get("description")
        status = self._parse_status(payload.extra_data.get("status"))

        record = await create_event(
            self._session,
            title=payload.content[:255],
            description=description,
            start_at=start_at,
            end_at=end_at,
            location=location,
            status=status,
            channel=payload.channel.value,
            sender=payload.sender,
        )

        external_id: str | None = None
        provider: str | None = None
        if self._google and self._calendar_id:
            try:
                event_body = self._build_google_event(
                    record.title, start_at, end_at, description, location
                )
                response = await self._google.insert_event(self._calendar_id, event_body)
                external_id = response.get("id") if isinstance(response, dict) else None
                provider = "google"
            except Exception as exc:  # pragma: no cover - external failure
                logger.warning("google_calendar_sync_failed", error=str(exc))
        elif self._caldav:
            try:
                await self._caldav.create_event(
                    {
                        "summary": record.title,
                        "description": description,
                        "start": start_at.isoformat(),
                        "end": end_at.isoformat() if end_at else None,
                        "location": location,
                    }
                )
                provider = "caldav"
            except Exception as exc:  # pragma: no cover
                logger.warning("caldav_sync_failed", error=str(exc))

        if external_id:
            record.external_id = external_id
            self._session.add(record)

        logger.info(
            "calendar_event_recorded",
            event_id=record.id,
            provider=provider or "local",
            start_at=start_at.isoformat(),
        )

        return {
            "status": "created",
            "event_id": record.id,
            "external_id": external_id,
            "start_at": start_at.isoformat(),
            "response": f"Evento agendado com sucesso: '{payload.content[:100]}{'...' if len(payload.content) > 100 else ''}'. " +
                       f"Data: {start_at.strftime('%d/%m/%Y às %H:%M')}",
        }

    def _parse_datetime(self, value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            parsed = value
        elif isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        else:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=self._default_timezone)
        return parsed

    def _build_google_event(
        self,
        title: str,
        start_at: datetime,
        end_at: datetime | None,
        description: str | None,
        location: str | None,
    ) -> dict[str, Any]:
        event = {
            "summary": title,
            "start": {"dateTime": start_at.isoformat()},
            "end": {"dateTime": (end_at or start_at).isoformat()},
        }
        if description:
            event["description"] = description
        if location:
            event["location"] = location
        return event

    def _parse_status(self, value: Any) -> EventStatus:
        if isinstance(value, str):
            try:
                return EventStatus[value.upper()]
            except KeyError:
                return EventStatus.CONFIRMED
        return EventStatus.CONFIRMED


__all__ = ["CalendarService"]
