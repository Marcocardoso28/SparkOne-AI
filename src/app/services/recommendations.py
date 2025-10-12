"""Recommendation service (e.g., places) with optional Google Places API.

If `google_places_api_key` is not configured, the service returns an
informative 501-like result to the caller.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings


class RecommendationsService:
    """Provide recommendation features (places, etc.)."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._api_key = self._settings.google_places_api_key

    async def search_places(
        self,
        query: str,
        *,
        lat: float | None = None,
        lng: float | None = None,
        radius_m: int = 4000,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search places using Google Places v1 if API key is available.

        Returns a normalized payload with `items` list.
        """
        if not self._api_key:
            return {
                "items": [],
                "message": "Google Places API key not configured. Set GOOGLE_PLACES_API_KEY to enable.",
                "enabled": False,
            }

        # Google Places v1: https://developers.google.com/maps/documentation/places/web-service/search-text
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "X-Goog-Api-Key": self._api_key,
            # Fields we care about
            "X-Goog-FieldMask": (
                "places.id,places.displayName.text,places.rating,places.formattedAddress,"
                "places.location,places.primaryTypeDisplayName.text"
            ),
        }
        payload: dict[str, Any] = {"textQuery": query}
        if lat is not None and lng is not None:
            payload["locationBias"] = {"circle": {"center": {"latitude": lat, "longitude": lng}, "radius": radius_m}}

        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        items: list[dict[str, Any]] = []
        for place in data.get("places", [])[:limit]:
            loc = place.get("location", {})
            items.append(
                {
                    "id": place.get("id"),
                    "name": place.get("displayName", {}).get("text"),
                    "address": place.get("formattedAddress"),
                    "rating": place.get("rating"),
                    "type": place.get("primaryTypeDisplayName", {}).get("text"),
                    "lat": loc.get("latitude"),
                    "lng": loc.get("longitude"),
                }
            )

        return {"items": items, "enabled": True}


__all__ = ["RecommendationsService"]

