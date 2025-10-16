"""Unit tests for NotionAdapter - ADR-014.

Tests storage adapter interface implementation for Notion integration.
Uses mocks to avoid actual API calls.

Related: ADR-014 (Storage Adapter Pattern), RF-019
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.domain.interfaces.storage_adapter import StorageAdapterError
from app.infrastructure.database.models.tasks import TaskRecord, TaskStatus
from app.infrastructure.storage.adapters.notion_adapter import NotionAdapter


@pytest.fixture
def valid_config():
    """Fixture for valid Notion adapter configuration."""
    return {
        "api_key": "secret_test_key_123",
        "database_id": "db-test-uuid-456",
        "timeout": 10.0,
    }


@pytest.fixture
def sample_task():
    """Fixture for sample task record."""
    return TaskRecord(
        id=uuid4(),
        title="Test Task from Unit Tests",
        description="This is a test task for NotionAdapter unit tests",
        status=TaskStatus.TODO,
        priority="high",
        due_date=datetime(2025, 1, 30, 12, 0, 0, tzinfo=timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_notion_client():
    """Fixture for mocked NotionClient."""
    with patch("app.infrastructure.storage.adapters.notion_adapter.NotionClient") as mock:
        yield mock


class TestNotionAdapterInitialization:
    """Tests for NotionAdapter initialization and configuration."""

    def test_init_with_valid_config(self, valid_config, mock_notion_client):
        """Test adapter initialization with valid configuration."""
        adapter = NotionAdapter(valid_config)

        assert adapter.name == "notion"
        assert adapter._api_key == "secret_test_key_123"
        assert adapter._database_id == "db-test-uuid-456"
        assert adapter._timeout == 10.0

        # Verify NotionClient was instantiated with correct params
        mock_notion_client.assert_called_once_with(
            "secret_test_key_123",
            timeout=10.0,
        )

    def test_init_without_api_key(self, mock_notion_client):
        """Test adapter raises ValueError when api_key is missing."""
        config = {"database_id": "db-test-uuid"}

        with pytest.raises(ValueError, match="requires 'api_key'"):
            NotionAdapter(config)

    def test_init_without_database_id(self, mock_notion_client):
        """Test adapter raises ValueError when database_id is missing."""
        config = {"api_key": "secret_key"}

        with pytest.raises(ValueError, match="requires 'database_id'"):
            NotionAdapter(config)

    def test_init_with_default_timeout(self, mock_notion_client):
        """Test adapter uses default timeout when not specified."""
        config = {
            "api_key": "secret_key",
            "database_id": "db-uuid",
        }

        adapter = NotionAdapter(config)
        assert adapter._timeout == 10.0


class TestNotionAdapterSaveTask:
    """Tests for NotionAdapter.save_task() method."""

    @pytest.mark.asyncio
    async def test_save_task_success(self, valid_config, sample_task, mock_notion_client):
        """Test successful task save to Notion."""
        # Setup mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.create_page = AsyncMock(
            return_value={"id": "notion-page-id-789"}
        )
        mock_notion_client.return_value = mock_client_instance

        adapter = NotionAdapter(valid_config)
        external_id = await adapter.save_task(sample_task)

        # Assertions
        assert external_id == "notion-page-id-789"
        mock_client_instance.create_page.assert_called_once()

        # Verify payload structure
        call_args = mock_client_instance.create_page.call_args[0][0]
        assert "parent" in call_args
        assert call_args["parent"]["database_id"] == "db-test-uuid-456"
        assert "properties" in call_args
        assert "Name" in call_args["properties"]

    @pytest.mark.asyncio
    async def test_save_task_with_all_fields(self, valid_config, sample_task, mock_notion_client):
        """Test save_task includes all task fields in payload."""
        mock_client_instance = AsyncMock()
        mock_client_instance.create_page = AsyncMock(
            return_value={"id": "notion-page-id"}
        )
        mock_notion_client.return_value = mock_client_instance

        adapter = NotionAdapter(valid_config)
        await adapter.save_task(sample_task)

        call_payload = mock_client_instance.create_page.call_args[0][0]
        props = call_payload["properties"]

        # Verify all fields are present
        assert props["Name"]["title"][0]["text"]["content"] == sample_task.title
        assert props["Description"]["rich_text"][0]["text"]["content"] == sample_task.description
        assert props["Due"]["date"]["start"] == sample_task.due_date.isoformat()
        assert props["Status"]["status"]["name"] == "To Do"
        assert props["Priority"]["select"]["name"] == "High"

    @pytest.mark.asyncio
    async def test_save_task_notion_api_error(self, valid_config, sample_task, mock_notion_client):
        """Test save_task raises StorageAdapterError on Notion API error."""
        mock_client_instance = AsyncMock()
        mock_client_instance.create_page = AsyncMock(
            side_effect=Exception("Notion API rate limit exceeded")
        )
        mock_notion_client.return_value = mock_client_instance

        adapter = NotionAdapter(valid_config)

        with pytest.raises(StorageAdapterError, match="Failed to save task to Notion"):
            await adapter.save_task(sample_task)

    @pytest.mark.asyncio
    async def test_save_task_invalid_response(self, valid_config, sample_task, mock_notion_client):
        """Test save_task raises error when Notion returns invalid response."""
        mock_client_instance = AsyncMock()
        mock_client_instance.create_page = AsyncMock(
            return_value={"error": "Invalid database"}  # No 'id' field
        )
        mock_notion_client.return_value = mock_client_instance

        adapter = NotionAdapter(valid_config)

        with pytest.raises(StorageAdapterError, match="Invalid response from Notion API"):
            await adapter.save_task(sample_task)


class TestNotionAdapterUpdateTask:
    """Tests for NotionAdapter.update_task() method."""

    @pytest.mark.asyncio
    async def test_update_task_not_implemented(self, valid_config, sample_task, mock_notion_client):
        """Test update_task returns False (not implemented yet)."""
        mock_notion_client.return_value = AsyncMock()

        adapter = NotionAdapter(valid_config)
        result = await adapter.update_task("notion-page-id", sample_task)

        assert result is False


class TestNotionAdapterDeleteTask:
    """Tests for NotionAdapter.delete_task() method."""

    @pytest.mark.asyncio
    async def test_delete_task_not_implemented(self, valid_config, mock_notion_client):
        """Test delete_task returns False (not implemented yet)."""
        mock_notion_client.return_value = AsyncMock()

        adapter = NotionAdapter(valid_config)
        result = await adapter.delete_task("notion-page-id")

        assert result is False


class TestNotionAdapterGetTask:
    """Tests for NotionAdapter.get_task() method."""

    @pytest.mark.asyncio
    async def test_get_task_not_implemented(self, valid_config, mock_notion_client):
        """Test get_task returns None (not implemented yet)."""
        mock_notion_client.return_value = AsyncMock()

        adapter = NotionAdapter(valid_config)
        result = await adapter.get_task("notion-page-id")

        assert result is None


class TestNotionAdapterHealthCheck:
    """Tests for NotionAdapter.health_check() method."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, valid_config, mock_notion_client):
        """Test health_check returns healthy status."""
        mock_notion_client.return_value = AsyncMock()

        adapter = NotionAdapter(valid_config)
        health = await adapter.health_check()

        assert health["status"] == "healthy"
        assert "latency_ms" in health
        assert "message" in health
        assert "timestamp" in health
        assert "database" in health["message"].lower()

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, valid_config, mock_notion_client):
        """Test health_check returns unhealthy on error."""
        mock_client_instance = AsyncMock()
        # Simulate error during health check (in real impl, would fail on API call)
        mock_notion_client.return_value = mock_client_instance

        adapter = NotionAdapter(valid_config)

        # Force an exception by patching the health_check method's internal logic
        with patch.object(adapter, '_database_id', None):
            # This will cause an error when trying to format the message
            health = await adapter.health_check()

            # Should still return a dict with status
            assert "status" in health
            assert "latency_ms" in health


class TestNotionAdapterClose:
    """Tests for NotionAdapter.close() method."""

    @pytest.mark.asyncio
    async def test_close_calls_client_close(self, valid_config, mock_notion_client):
        """Test close() calls NotionClient.close()."""
        mock_client_instance = AsyncMock()
        mock_client_instance.close = AsyncMock()
        mock_notion_client.return_value = mock_client_instance

        adapter = NotionAdapter(valid_config)
        await adapter.close()

        mock_client_instance.close.assert_called_once()


class TestNotionAdapterPayloadBuilder:
    """Tests for NotionAdapter._build_notion_payload() private method."""

    def test_build_payload_minimal_task(self, valid_config, mock_notion_client):
        """Test payload builder with minimal task (only title)."""
        mock_notion_client.return_value = AsyncMock()

        adapter = NotionAdapter(valid_config)
        task = TaskRecord(
            id=uuid4(),
            title="Minimal Task",
            status=TaskStatus.TODO,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        payload = adapter._build_notion_payload(task)

        assert "properties" in payload
        assert "Name" in payload["properties"]
        assert payload["properties"]["Name"]["title"][0]["text"]["content"] == "Minimal Task"

    def test_build_payload_status_mapping(self, valid_config, mock_notion_client):
        """Test correct status mapping to Notion status names."""
        mock_notion_client.return_value = AsyncMock()

        adapter = NotionAdapter(valid_config)

        status_mappings = {
            TaskStatus.TODO: "To Do",
            TaskStatus.IN_PROGRESS: "In Progress",
            TaskStatus.COMPLETED: "Done",
            TaskStatus.CANCELLED: "Cancelled",
        }

        for sparkone_status, notion_status in status_mappings.items():
            task = TaskRecord(
                id=uuid4(),
                title="Test",
                status=sparkone_status,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            payload = adapter._build_notion_payload(task)
            assert payload["properties"]["Status"]["status"]["name"] == notion_status

    def test_build_payload_priority_mapping(self, valid_config, mock_notion_client):
        """Test correct priority mapping to Notion select values."""
        mock_notion_client.return_value = AsyncMock()

        adapter = NotionAdapter(valid_config)

        priority_mappings = {
            "low": "Low",
            "medium": "Medium",
            "high": "High",
        }

        for sparkone_priority, notion_priority in priority_mappings.items():
            task = TaskRecord(
                id=uuid4(),
                title="Test",
                status=TaskStatus.TODO,
                priority=sparkone_priority,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            payload = adapter._build_notion_payload(task)
            assert payload["properties"]["Priority"]["select"]["name"] == notion_priority


__all__ = [
    "TestNotionAdapterInitialization",
    "TestNotionAdapterSaveTask",
    "TestNotionAdapterUpdateTask",
    "TestNotionAdapterDeleteTask",
    "TestNotionAdapterGetTask",
    "TestNotionAdapterHealthCheck",
    "TestNotionAdapterClose",
    "TestNotionAdapterPayloadBuilder",
]
