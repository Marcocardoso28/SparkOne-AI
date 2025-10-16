"""Unit tests for GoogleSheetsAdapter - ADR-014.

Tests storage adapter interface implementation for Google Sheets integration.
Uses mocks to avoid actual API calls.

Related: ADR-014 (Storage Adapter Pattern), RF-019
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.domain.interfaces.storage_adapter import StorageAdapterError
from app.infrastructure.database.models.tasks import TaskRecord, TaskStatus
from app.infrastructure.storage.adapters.sheets_adapter import GoogleSheetsAdapter


@pytest.fixture
def valid_config():
    """Fixture for valid Google Sheets adapter configuration."""
    return {
        "credentials_path": "/path/to/credentials.json",
        "spreadsheet_id": "1abc123xyz",
        "sheet_name": "Tasks",
        "header_row": 1,
    }


@pytest.fixture
def sample_task():
    """Fixture for sample task record."""
    return TaskRecord(
        id=uuid4(),
        title="Test Sheets Task",
        description="Google Sheets adapter unit test task",
        status=TaskStatus.TODO,
        priority="low",
        due_date=datetime(2025, 3, 10, 9, 0, 0, tzinfo=timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_sheets_client():
    """Fixture for mocked GoogleSheetsClient."""
    with patch("app.infrastructure.storage.adapters.sheets_adapter.GoogleSheetsClient") as mock:
        yield mock


class TestGoogleSheetsAdapterInitialization:
    """Tests for GoogleSheetsAdapter initialization and configuration."""

    def test_init_with_valid_config(self, valid_config, mock_sheets_client):
        """Test adapter initialization with valid configuration."""
        adapter = GoogleSheetsAdapter(valid_config)

        assert adapter.name == "sheets"
        assert adapter._credentials_path == "/path/to/credentials.json"
        assert adapter._spreadsheet_id == "1abc123xyz"
        assert adapter._sheet_name == "Tasks"
        assert adapter._header_row == 1

        # Verify GoogleSheetsClient was instantiated
        mock_sheets_client.assert_called_once_with("/path/to/credentials.json")

    def test_init_without_credentials_path(self):
        """Test adapter raises ValueError when credentials_path is missing."""
        config = {"spreadsheet_id": "1abc123"}

        with pytest.raises(ValueError, match="requires 'credentials_path'"):
            GoogleSheetsAdapter(config)

    def test_init_without_spreadsheet_id(self):
        """Test adapter raises ValueError when spreadsheet_id is missing."""
        config = {"credentials_path": "/path/to/creds.json"}

        with pytest.raises(ValueError, match="requires 'spreadsheet_id'"):
            GoogleSheetsAdapter(config)

    def test_init_with_default_sheet_name(self, mock_sheets_client):
        """Test adapter uses default sheet_name when not specified."""
        config = {
            "credentials_path": "/path/to/creds.json",
            "spreadsheet_id": "1abc",
        }

        adapter = GoogleSheetsAdapter(config)
        assert adapter._sheet_name == "Tasks"

    def test_init_with_default_header_row(self, mock_sheets_client):
        """Test adapter uses default header_row when not specified."""
        config = {
            "credentials_path": "/path/to/creds.json",
            "spreadsheet_id": "1abc",
        }

        adapter = GoogleSheetsAdapter(config)
        assert adapter._header_row == 1


class TestGoogleSheetsAdapterSaveTask:
    """Tests for GoogleSheetsAdapter.save_task() method."""

    @pytest.mark.asyncio
    async def test_save_task_success(self, valid_config, sample_task, mock_sheets_client):
        """Test successful task save to Google Sheets."""
        # Setup mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.append_row = AsyncMock()
        mock_sheets_client.return_value = mock_client_instance

        adapter = GoogleSheetsAdapter(valid_config)
        row_id = await adapter.save_task(sample_task)

        # Assertions
        assert row_id.startswith("row_")
        mock_client_instance.append_row.assert_called_once()

        # Verify range and values
        call_args = mock_client_instance.append_row.call_args[0]
        assert call_args[0] == "1abc123xyz"  # spreadsheet_id
        assert call_args[1] == "Tasks!A:G"  # range_name
        assert len(call_args[2]) == 7  # 7 columns

    @pytest.mark.asyncio
    async def test_save_task_with_all_fields(self, valid_config, sample_task, mock_sheets_client):
        """Test save_task includes all task fields in row."""
        mock_client_instance = AsyncMock()
        mock_client_instance.append_row = AsyncMock()
        mock_sheets_client.return_value = mock_client_instance

        adapter = GoogleSheetsAdapter(valid_config)
        await adapter.save_task(sample_task)

        call_values = mock_client_instance.append_row.call_args[0][2]

        # Verify row structure
        assert call_values[1] == sample_task.title  # Column B: Title
        assert call_values[2] == sample_task.description  # Column C: Description
        assert call_values[3] == sample_task.status  # Column D: Status
        assert call_values[4] == sample_task.priority  # Column E: Priority
        assert sample_task.due_date.isoformat() in call_values[5]  # Column F: Due Date

    @pytest.mark.asyncio
    async def test_save_task_api_error(self, valid_config, sample_task, mock_sheets_client):
        """Test save_task raises StorageAdapterError on API error."""
        mock_client_instance = AsyncMock()
        mock_client_instance.append_row = AsyncMock(
            side_effect=Exception("Sheets API quota exceeded")
        )
        mock_sheets_client.return_value = mock_client_instance

        adapter = GoogleSheetsAdapter(valid_config)

        with pytest.raises(StorageAdapterError, match="Failed to save task to Google Sheets"):
            await adapter.save_task(sample_task)


class TestGoogleSheetsAdapterUpdateTask:
    """Tests for GoogleSheetsAdapter.update_task() method."""

    @pytest.mark.asyncio
    async def test_update_task_not_implemented(self, valid_config, sample_task, mock_sheets_client):
        """Test update_task returns False (not implemented yet)."""
        mock_sheets_client.return_value = AsyncMock()

        adapter = GoogleSheetsAdapter(valid_config)
        result = await adapter.update_task("row_123", sample_task)

        assert result is False


class TestGoogleSheetsAdapterDeleteTask:
    """Tests for GoogleSheetsAdapter.delete_task() method."""

    @pytest.mark.asyncio
    async def test_delete_task_not_implemented(self, valid_config, mock_sheets_client):
        """Test delete_task returns False (not implemented yet)."""
        mock_sheets_client.return_value = AsyncMock()

        adapter = GoogleSheetsAdapter(valid_config)
        result = await adapter.delete_task("row_123")

        assert result is False


class TestGoogleSheetsAdapterGetTask:
    """Tests for GoogleSheetsAdapter.get_task() method."""

    @pytest.mark.asyncio
    async def test_get_task_not_implemented(self, valid_config, mock_sheets_client):
        """Test get_task returns None (not implemented yet)."""
        mock_sheets_client.return_value = AsyncMock()

        adapter = GoogleSheetsAdapter(valid_config)
        result = await adapter.get_task("row_123")

        assert result is None


class TestGoogleSheetsAdapterHealthCheck:
    """Tests for GoogleSheetsAdapter.health_check() method."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, valid_config, mock_sheets_client):
        """Test health_check returns healthy status when sheet is accessible."""
        mock_client_instance = AsyncMock()
        mock_client_instance.list_rows = AsyncMock(
            return_value=[["ID", "Title", "Description", "Status", "Priority", "Due Date", "Created"]]
        )
        mock_sheets_client.return_value = mock_client_instance

        adapter = GoogleSheetsAdapter(valid_config)
        health = await adapter.health_check()

        assert health["status"] == "healthy"
        assert "latency_ms" in health
        assert "message" in health
        assert "timestamp" in health
        assert "Tasks" in health["message"]

    @pytest.mark.asyncio
    async def test_health_check_degraded(self, valid_config, mock_sheets_client):
        """Test health_check returns degraded when sheet is empty."""
        mock_client_instance = AsyncMock()
        mock_client_instance.list_rows = AsyncMock(return_value=[])
        mock_sheets_client.return_value = mock_client_instance

        adapter = GoogleSheetsAdapter(valid_config)
        health = await adapter.health_check()

        assert health["status"] == "degraded"
        assert "empty" in health["message"]

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, valid_config, mock_sheets_client):
        """Test health_check returns unhealthy on error."""
        mock_client_instance = AsyncMock()
        mock_client_instance.list_rows = AsyncMock(
            side_effect=Exception("Credentials invalid")
        )
        mock_sheets_client.return_value = mock_client_instance

        adapter = GoogleSheetsAdapter(valid_config)
        health = await adapter.health_check()

        assert health["status"] == "unhealthy"
        assert "unreachable" in health["message"].lower()


class TestGoogleSheetsAdapterBatchImport:
    """Tests for GoogleSheetsAdapter.batch_import_from_sheet() method."""

    @pytest.mark.asyncio
    async def test_batch_import_success(self, valid_config, mock_sheets_client):
        """Test successful batch import from Google Sheets."""
        mock_client_instance = AsyncMock()
        mock_client_instance.list_rows = AsyncMock(
            return_value=[
                ["row_1", "Task 1", "Description 1", "pending", "high", "2025-04-01T10:00:00Z", "2025-01-27T12:00:00Z"],
                ["row_2", "Task 2", "Description 2", "in_progress", "medium", "", "2025-01-27T13:00:00Z"],
            ]
        )
        mock_sheets_client.return_value = mock_client_instance

        adapter = GoogleSheetsAdapter(valid_config)
        tasks = await adapter.batch_import_from_sheet()

        assert len(tasks) == 2
        assert tasks[0].title == "Task 1"
        assert tasks[0].status == "pending"
        assert tasks[0].priority == "high"
        assert tasks[1].title == "Task 2"
        assert tasks[1].status == "in_progress"

    @pytest.mark.asyncio
    async def test_batch_import_skips_invalid_rows(self, valid_config, mock_sheets_client):
        """Test batch_import skips rows with insufficient data."""
        mock_client_instance = AsyncMock()
        mock_client_instance.list_rows = AsyncMock(
            return_value=[
                ["row_1"],  # Only ID, no title - should skip
                ["row_2", "Valid Task", "Desc", "pending", "medium", "", ""],  # Valid
            ]
        )
        mock_sheets_client.return_value = mock_client_instance

        adapter = GoogleSheetsAdapter(valid_config)
        tasks = await adapter.batch_import_from_sheet()

        # Should only import the valid row
        assert len(tasks) == 1
        assert tasks[0].title == "Valid Task"

    @pytest.mark.asyncio
    async def test_batch_import_api_error(self, valid_config, mock_sheets_client):
        """Test batch_import raises StorageAdapterError on API error."""
        mock_client_instance = AsyncMock()
        mock_client_instance.list_rows = AsyncMock(
            side_effect=Exception("Sheets API permission denied")
        )
        mock_sheets_client.return_value = mock_client_instance

        adapter = GoogleSheetsAdapter(valid_config)

        with pytest.raises(StorageAdapterError, match="Failed to import from Google Sheets"):
            await adapter.batch_import_from_sheet()


class TestGoogleSheetsAdapterRowBuilder:
    """Tests for GoogleSheetsAdapter._build_sheets_row() private method."""

    def test_build_row_complete_task(self, valid_config, sample_task, mock_sheets_client):
        """Test building row with complete task data."""
        mock_sheets_client.return_value = AsyncMock()

        adapter = GoogleSheetsAdapter(valid_config)
        row = adapter._build_sheets_row(sample_task, "row_test_123")

        assert len(row) == 7
        assert row[0] == "row_test_123"  # Row ID
        assert row[1] == sample_task.title
        assert row[2] == sample_task.description
        assert row[3] == sample_task.status
        assert row[4] == sample_task.priority
        assert sample_task.due_date.isoformat() in row[5]
        assert "Z" in row[6]  # Timestamp format

    def test_build_row_minimal_task(self, valid_config, mock_sheets_client):
        """Test building row with minimal task (only required fields)."""
        mock_sheets_client.return_value = AsyncMock()

        adapter = GoogleSheetsAdapter(valid_config)
        task = TaskRecord(
            id=uuid4(),
            title="Minimal Task",
            status=TaskStatus.TODO,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        row = adapter._build_sheets_row(task, "row_min_123")

        assert row[0] == "row_min_123"
        assert row[1] == "Minimal Task"
        assert row[2] == ""  # No description
        assert row[3] == "todo"
        assert row[4] == "medium"  # Default priority
        assert row[5] == ""  # No due date


class TestGoogleSheetsAdapterRowParser:
    """Tests for GoogleSheetsAdapter._parse_sheets_row() private method."""

    def test_parse_row_complete(self, valid_config, mock_sheets_client):
        """Test parsing complete row data."""
        mock_sheets_client.return_value = AsyncMock()

        adapter = GoogleSheetsAdapter(valid_config)
        row = [
            "row_parsed_123",
            "Parsed Task",
            "Description here",
            "completed",
            "high",
            "2025-05-01T14:30:00Z",
            "2025-01-27T10:00:00Z",
        ]

        task = adapter._parse_sheets_row(row)

        assert task.external_id == "row_parsed_123"
        assert task.title == "Parsed Task"
        assert task.description == "Description here"
        assert task.status == "completed"
        assert task.priority == "high"
        assert task.due_date is not None
        assert task.channel == "sheets"
        assert task.sender == "sheets_sync"

    def test_parse_row_minimal(self, valid_config, mock_sheets_client):
        """Test parsing minimal row (ID and title only)."""
        mock_sheets_client.return_value = AsyncMock()

        adapter = GoogleSheetsAdapter(valid_config)
        row = ["row_min", "Minimal"]

        task = adapter._parse_sheets_row(row)

        assert task.external_id == "row_min"
        assert task.title == "Minimal"
        assert task.status == "pending"  # default
        assert task.priority == "medium"  # default
        assert task.due_date is None

    def test_parse_row_with_empty_fields(self, valid_config, mock_sheets_client):
        """Test parsing row with empty optional fields."""
        mock_sheets_client.return_value = AsyncMock()

        adapter = GoogleSheetsAdapter(valid_config)
        row = ["row_123", "Task", "", "", ""]

        task = adapter._parse_sheets_row(row)

        assert task.title == "Task"
        assert task.description is None
        assert task.status == "pending"
        assert task.priority == "medium"

    def test_parse_row_invalid_date(self, valid_config, mock_sheets_client):
        """Test parsing row with invalid date format."""
        mock_sheets_client.return_value = AsyncMock()

        adapter = GoogleSheetsAdapter(valid_config)
        row = ["row_123", "Task", "Desc", "pending", "medium", "invalid-date"]

        task = adapter._parse_sheets_row(row)

        # Should handle invalid date gracefully
        assert task.due_date is None


__all__ = [
    "TestGoogleSheetsAdapterInitialization",
    "TestGoogleSheetsAdapterSaveTask",
    "TestGoogleSheetsAdapterUpdateTask",
    "TestGoogleSheetsAdapterDeleteTask",
    "TestGoogleSheetsAdapterGetTask",
    "TestGoogleSheetsAdapterHealthCheck",
    "TestGoogleSheetsAdapterBatchImport",
    "TestGoogleSheetsAdapterRowBuilder",
    "TestGoogleSheetsAdapterRowParser",
]
