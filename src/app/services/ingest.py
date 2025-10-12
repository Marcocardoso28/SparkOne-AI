"""Compatibility wrapper for ingestion service used by tests.

Provides a patchable `ingest_message` function so tests can stub ingestion
without hitting the database. The real implementation lives on
`IngestionService.ingest`.
"""

from __future__ import annotations

from typing import Any

from app.models.schemas import ChannelMessage

try:
    # Imported at call time to avoid circulars in application bootstrap
    from app.services.ingestion import IngestionService as _IngestionServiceImpl  # type: ignore
except Exception:  # pragma: no cover - fallback for import timing issues in tests
    _IngestionServiceImpl = None  # type: ignore[assignment]


async def ingest_message(message: ChannelMessage, ingestion: Any | None = None) -> None:
    """Thin wrapper around `IngestionService.ingest`.

    Tests patch this function to avoid touching external systems.
    """
    if ingestion is None:
        # Defer import to avoid heavy dependencies when patched in tests
        from app.dependencies import get_ingestion_service  # local import

        ingestion = await get_ingestion_service()

    # If the real service was provided or resolved, delegate to it
    if hasattr(ingestion, "ingest"):
        await ingestion.ingest(message)  # type: ignore[attr-defined]
        return

    # Last-resort: if an unexpected object is provided, do nothing
    return None


__all__ = ["ingest_message"]

