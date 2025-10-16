"""Google Sheets Storage Adapter - ADR-014.

Implements storage adapter interface for Google Sheets integration.
Handles task synchronization between SparkOne and Google Sheets spreadsheets.

Related ADR: ADR-014 (Storage Adapter Pattern)
Related RF: RF-019 (Multi-Storage Backend System)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.domain.interfaces.storage_adapter import StorageAdapter, StorageAdapterError
from app.infrastructure.database.models.tasks import TaskRecord
from app.infrastructure.integrations.google_sheets import GoogleSheetsClient

logger = logging.getLogger(__name__)


class GoogleSheetsAdapter(StorageAdapter):
    """Storage adapter for Google Sheets integration.

    Synchronizes tasks between SparkOne local database and Google Sheets spreadsheets.
    Uses Google Sheets API v4 via service account authentication.

    Configuration:
        - credentials_path: Path to Google service account JSON file
        - spreadsheet_id: Google Sheets spreadsheet ID
        - sheet_name: Sheet name/range (default: "Tasks")
        - header_row: Row number for headers (default: 1)

    Example:
        ```python
        config = {
            "credentials_path": "/path/to/credentials.json",
            "spreadsheet_id": "1abc...xyz",
            "sheet_name": "Tasks",
            "header_row": 1
        }
        adapter = GoogleSheetsAdapter(config)
        row_id = await adapter.save_task(task)
        ```

    Sheet Format:
        Column A: Task ID (external_id)
        Column B: Title
        Column C: Description
        Column D: Status
        Column E: Priority
        Column F: Due Date (ISO format)
        Column G: Created At
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize Google Sheets adapter with configuration.

        Args:
            config: Configuration dictionary with keys:
                - credentials_path (str): Path to service account JSON
                - spreadsheet_id (str): Google Sheets spreadsheet ID
                - sheet_name (str, optional): Sheet name (default: "Tasks")
                - header_row (int, optional): Header row number (default: 1)

        Raises:
            ValueError: If required config keys are missing
        """
        if "credentials_path" not in config:
            raise ValueError("GoogleSheets adapter requires 'credentials_path' in config")
        if "spreadsheet_id" not in config:
            raise ValueError("GoogleSheets adapter requires 'spreadsheet_id' in config")

        self._credentials_path = config["credentials_path"]
        self._spreadsheet_id = config["spreadsheet_id"]
        self._sheet_name = config.get("sheet_name", "Tasks")
        self._header_row = config.get("header_row", 1)

        self._client = GoogleSheetsClient(self._credentials_path)

        logger.info(
            f"Initialized GoogleSheetsAdapter with spreadsheet "
            f"{self._spreadsheet_id[:10]}... sheet '{self._sheet_name}'"
        )

    @property
    def name(self) -> str:
        """Return adapter name.

        Returns:
            str: 'sheets'
        """
        return "sheets"

    async def save_task(self, task: TaskRecord) -> str:
        """Save task to Google Sheets.

        Appends a new row to the spreadsheet.

        Args:
            task: The task record to save

        Returns:
            str: Row ID (row number as string)

        Raises:
            StorageAdapterError: If save operation fails

        Example:
            >>> task = TaskRecord(title="Buy groceries", status="pending")
            >>> row_id = await adapter.save_task(task)
            >>> print(row_id)
            '5'  # Row number in sheet
        """
        try:
            # Generate unique ID for this row (timestamp-based)
            row_id = f"row_{int(datetime.utcnow().timestamp() * 1000)}"

            # Build row values
            values = self._build_sheets_row(task, row_id)

            # Append to sheet
            range_name = f"{self._sheet_name}!A:G"
            await self._client.append_row(
                self._spreadsheet_id,
                range_name,
                values
            )

            logger.info(
                f"Saved task to Google Sheets: {task.title[:50]} -> {row_id}"
            )
            return row_id

        except Exception as e:
            if isinstance(e, StorageAdapterError):
                raise
            raise StorageAdapterError(
                f"Failed to save task to Google Sheets: {e}",
                adapter_name=self.name,
                original_error=e,
            ) from e

    async def update_task(self, external_id: str, task: TaskRecord) -> bool:
        """Update existing task in Google Sheets.

        Note:
            Requires finding the row by external_id and updating it.
            Current GoogleSheetsClient only supports append.
            This is a placeholder for future implementation.

        Args:
            external_id: Row ID from save_task()
            task: Updated task record

        Returns:
            bool: False (not implemented yet)

        Todo:
            - Implement update() method in GoogleSheetsClient
            - Add row search by external_id
            - Update specific row values
        """
        logger.warning(
            f"GoogleSheetsAdapter.update_task() not implemented yet (row_id: {external_id})"
        )
        return False

    async def delete_task(self, external_id: str) -> bool:
        """Delete task from Google Sheets.

        Note:
            Requires finding the row by external_id and deleting it.
            Current GoogleSheetsClient doesn't support row deletion.
            This is a placeholder for future implementation.

        Args:
            external_id: Row ID from save_task()

        Returns:
            bool: False (not implemented yet)

        Todo:
            - Implement delete_row() method in GoogleSheetsClient
            - Add row search by external_id
            - Delete specific row (or mark as deleted)
        """
        logger.warning(
            f"GoogleSheetsAdapter.delete_task() not implemented yet (row_id: {external_id})"
        )
        return False

    async def get_task(self, external_id: str) -> TaskRecord | None:
        """Retrieve task from Google Sheets.

        Note:
            Requires searching rows by external_id.
            Current GoogleSheetsClient only supports list_rows.
            This is a placeholder for future implementation.

        Args:
            external_id: Row ID from save_task()

        Returns:
            TaskRecord | None: None (not implemented yet)

        Todo:
            - Search rows for matching external_id (column A)
            - Parse row to TaskRecord
            - Return parsed task
        """
        logger.warning(
            f"GoogleSheetsAdapter.get_task() not implemented yet (row_id: {external_id})"
        )
        return None

    async def health_check(self) -> dict[str, Any]:
        """Check Google Sheets API connectivity and health.

        Performs a lightweight test to verify Sheets API is accessible.

        Returns:
            dict: Health status with keys:
                - status: 'healthy' | 'degraded' | 'unhealthy'
                - latency_ms: Round-trip latency
                - message: Human-readable status
                - timestamp: ISO timestamp

        Example:
            >>> health = await adapter.health_check()
            >>> print(health['status'])
            'healthy'
        """
        import time

        start = time.time()
        try:
            # Try to read the header row to verify access
            range_name = f"{self._sheet_name}!A{self._header_row}:G{self._header_row}"
            rows = await self._client.list_rows(self._spreadsheet_id, range_name)

            latency_ms = (time.time() - start) * 1000

            if rows:
                message = f"Google Sheets accessible (sheet: '{self._sheet_name}')"
                status = "healthy"
            else:
                message = f"Google Sheets accessible but sheet '{self._sheet_name}' may be empty"
                status = "degraded"

            return {
                "status": status,
                "latency_ms": round(latency_ms, 2),
                "message": message,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            logger.warning(f"Google Sheets health check failed: {e}")

            return {
                "status": "unhealthy",
                "latency_ms": round(latency_ms, 2),
                "message": f"Google Sheets API unreachable: {str(e)[:100]}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

    def _build_sheets_row(self, task: TaskRecord, row_id: str) -> list[Any]:
        """Build Google Sheets row values from task record.

        Args:
            task: Task record to convert
            row_id: Unique row identifier

        Returns:
            list: Row values [ID, Title, Description, Status, Priority, Due Date, Created At]
        """
        return [
            row_id,  # Column A: Row ID
            task.title,  # Column B: Title
            task.description or "",  # Column C: Description
            task.status or "pending",  # Column D: Status
            task.priority or "medium",  # Column E: Priority
            task.due_date.isoformat() if task.due_date else "",  # Column F: Due Date
            datetime.utcnow().isoformat() + "Z",  # Column G: Created At
        ]

    async def batch_import_from_sheet(self) -> list[TaskRecord]:
        """Import all tasks from Google Sheets to local database.

        Reads all rows from the sheet and converts them to TaskRecord objects.
        Useful for initial sync or bulk import.

        Returns:
            list[TaskRecord]: List of parsed tasks

        Raises:
            StorageAdapterError: If import operation fails

        Example:
            >>> tasks = await adapter.batch_import_from_sheet()
            >>> print(f"Imported {len(tasks)} tasks")
        """
        try:
            # Read all rows after header
            range_name = f"{self._sheet_name}!A{self._header_row + 1}:G"
            rows = await self._client.list_rows(self._spreadsheet_id, range_name)

            tasks: list[TaskRecord] = []
            for row in rows:
                if len(row) < 2:  # Need at least ID and Title
                    continue

                try:
                    task = self._parse_sheets_row(row)
                    tasks.append(task)
                except Exception as e:
                    logger.warning(f"Failed to parse row {row}: {e}")
                    continue

            logger.info(f"Imported {len(tasks)} tasks from Google Sheets")
            return tasks

        except Exception as e:
            raise StorageAdapterError(
                f"Failed to import from Google Sheets: {e}",
                adapter_name=self.name,
                original_error=e,
            ) from e

    def _parse_sheets_row(self, row: list[Any]) -> TaskRecord:
        """Parse Google Sheets row to TaskRecord.

        Args:
            row: Row values from sheet

        Returns:
            TaskRecord: Parsed task record
        """
        # Parse due date
        due_date = None
        if len(row) > 5 and row[5]:
            try:
                due_date = datetime.fromisoformat(row[5].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        return TaskRecord(
            external_id=row[0] if len(row) > 0 else None,
            title=row[1] if len(row) > 1 else "",
            description=row[2] if len(row) > 2 and row[2] else None,
            status=row[3] if len(row) > 3 and row[3] else "pending",
            priority=row[4] if len(row) > 4 and row[4] else "medium",
            due_date=due_date,
            channel="sheets",
            sender="sheets_sync",
        )


__all__ = ["GoogleSheetsAdapter"]
