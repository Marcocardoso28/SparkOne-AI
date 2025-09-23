"""Google Calendar integration wrapper."""

from __future__ import annotations

import asyncio
from typing import Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

CALENDAR_SCOPES = ("https://www.googleapis.com/auth/calendar",)


class GoogleCalendarClient:
    """Async-friendly wrapper around Google Calendar API v3."""

    def __init__(self, credentials_path: str) -> None:
        credentials = Credentials.from_service_account_file(credentials_path, scopes=CALENDAR_SCOPES)
        self._service = build("calendar", "v3", credentials=credentials, cache_discovery=False)

    async def insert_event(self, calendar_id: str, event: dict[str, Any]) -> dict[str, Any]:
        def _insert() -> dict[str, Any]:
            return (
                self._service.events()
                .insert(calendarId=calendar_id, body=event, sendUpdates="all")
                .execute()
            )

        return await asyncio.to_thread(_insert)

    async def list_events(self, calendar_id: str, time_min: str, time_max: str) -> list[dict[str, Any]]:
        def _list() -> list[dict[str, Any]]:
            result = (
                self._service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            return result.get("items", [])

        return await asyncio.to_thread(_list)


__all__ = ["GoogleCalendarClient", "CALENDAR_SCOPES"]
