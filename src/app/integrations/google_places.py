"""Google Places recommendation client."""

from __future__ import annotations

from typing import Any

import httpx


class GooglePlacesClient:  # pragma: no cover - http stub
    def __init__(self, api_key: str, *, timeout: float = 10.0) -> None:
        self._api_key = api_key
        self._client = httpx.AsyncClient(timeout=timeout)

    async def nearby_search(self, latitude: float, longitude: float, radius: int = 2000) -> dict[str, Any]:
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "key": self._api_key,
            "location": f"{latitude},{longitude}",
            "radius": radius,
        }
        response = await self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()


__all__ = ["GooglePlacesClient"]
