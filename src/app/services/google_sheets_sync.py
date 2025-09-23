"""Service that synchronizes Google Sheets rows into SparkOne."""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..channels import MessageNormalizer
from ..models.schemas import ChannelMessage
from ..models.db.repositories import update_sheets_sync_state, get_sheets_sync_state
from ..integrations.google_sheets import GoogleSheetsClient
from ..services.ingestion import IngestionService
from ..core.metrics import SHEETS_SYNC_COUNTER

logger = structlog.get_logger(__name__)


class GoogleSheetsSyncService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        client: GoogleSheetsClient,
        normalizer: MessageNormalizer,
        ingestion_service: IngestionService,
        spreadsheet_id: str,
        range_name: str,
    ) -> None:
        self._session = session
        self._client = client
        self._normalizer = normalizer
        self._ingestion = ingestion_service
        self._spreadsheet_id = spreadsheet_id
        self._range_name = range_name

    async def sync(self) -> dict[str, Any]:
        state = await get_sheets_sync_state(
            self._session,
            spreadsheet_id=self._spreadsheet_id,
            range_name=self._range_name,
        )
        last_row_index = state.last_row_index if state else 0
        rows = await self._client.list_rows(self._spreadsheet_id, self._range_name)
        processed = 0
        skipped = 0
        failures = 0
        last_processed_index = last_row_index
        for index, row in enumerate(rows, start=1):
            if index <= last_row_index:
                continue
            if not self._has_meaningful_values(row):
                skipped += 1
                continue
            payload = {
                "row": row,
                "sheet_id": self._spreadsheet_id,
                "user": "google_sheets",
                "row_index": index,
            }
            try:
                message: ChannelMessage = await self._normalizer.normalize("google_sheets", payload)
                await self._ingestion.ingest(message)
            except Exception as exc:  # pragma: no cover - ingestion failure path
                failures += 1
                logger.warning("sheets_row_failed", row_index=index, error=str(exc))
                continue
            last_processed_index = index
            processed += 1

        if processed:
            await update_sheets_sync_state(
                self._session,
                spreadsheet_id=self._spreadsheet_id,
                range_name=self._range_name,
                last_row_index=last_processed_index,
            )
            SHEETS_SYNC_COUNTER.labels(status="success").inc(processed)
        if skipped:
            SHEETS_SYNC_COUNTER.labels(status="skipped").inc(skipped)
        if failures:
            SHEETS_SYNC_COUNTER.labels(status="failure").inc(failures)
        if not processed and not skipped and not failures:
            SHEETS_SYNC_COUNTER.labels(status="skipped").inc()

        return {
            "processed": processed,
            "last_row_index": last_processed_index,
            "skipped": skipped,
            "failures": failures,
        }

    def _has_meaningful_values(self, row: list[Any]) -> bool:
        for cell in row:
            if isinstance(cell, str) and cell.strip():
                return True
            if cell not in (None, ""):
                return True
        return False


__all__ = ["GoogleSheetsSyncService"]
