"""Client wrapper for Evolution API (WhatsApp)."""

from __future__ import annotations

from typing import Any

import httpx


class EvolutionAPIClient:
    """Minimal Evolution API integration with async httpx client."""

    def __init__(self, base_url: str, token: str, *, timeout: float = 10.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={"Authorization": f"Bearer {token}"},
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    async def send_message(self, payload: dict[str, Any]) -> httpx.Response:  # pragma: no cover - http call
        response = await self._client.post("/messages", json=payload)
        response.raise_for_status()
        return response

    async def close(self) -> None:
        await self._client.aclose()


__all__ = ["EvolutionAPIClient"]
