"""Notion API client wrapper."""

from __future__ import annotations

from typing import Any

import httpx


class NotionClient:  # pragma: no cover - http stub
    """Partial Notion REST API wrapper for tasks."""

    def __init__(self, token: str, *, timeout: float = 10.0) -> None:
        self._client = httpx.AsyncClient(
            base_url="https://api.notion.com",
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    async def create_page(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._client.post("/v1/pages", json=payload)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()


__all__ = ["NotionClient"]
