"""CalDAV integration layer."""

from __future__ import annotations

from typing import Any


class CalDAVClient:  # pragma: no cover - placeholder
    """Placeholder CalDAV client; will wrap caldav library in the future."""

    def __init__(self, url: str, username: str, password: str) -> None:
        self._url = url
        self._username = username
        self._password = password

    async def create_event(self, event: dict[str, Any]) -> None:
        raise NotImplementedError("CalDAV integration not implemented")

    async def list_events(self, start: str, end: str) -> list[dict[str, Any]]:
        raise NotImplementedError("CalDAV integration not implemented")


__all__ = ["CalDAVClient"]
