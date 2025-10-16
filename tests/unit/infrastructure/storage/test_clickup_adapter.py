"""Unit tests for ClickUpAdapter - ADR-014.

Tests storage adapter interface implementation for ClickUp integration.
Uses httpx mocking to avoid actual API calls.

Related: ADR-014 (Storage Adapter Pattern), RF-019
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest

from app.domain.interfaces.storage_adapter import StorageAdapterError
from app.infrastructure.database.models.tasks import TaskRecord, TaskStatus
from app.infrastructure.storage.adapters.clickup_adapter import ClickUpAdapter


@pytest.fixture
def valid_config():
    """Fixture for valid ClickUp adapter configuration."""
    return {
        "api_key": "pk_test_key_123",
        "list_id": "123456789",
        "timeout": 10.0,
    }


@pytest.fixture
def sample_task():
    """Fixture for sample task record."""
    return TaskRecord(
        id=uuid4(),
        title="Test ClickUp Task",
        description="ClickUp adapter unit test task",
        status=TaskStatus.IN_PROGRESS,
        priority="medium",
        due_date=datetime(2025, 2, 15, 10, 0, 0, tzinfo=timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_httpx_client():
    """Fixture for mocked httpx AsyncClient."""
    with patch("httpx.AsyncClient") as mock:
        yield mock


class TestClickUpAdapterInitialization:
    """Tests for ClickUpAdapter initialization and configuration."""

    def test_init_with_valid_config(self, valid_config, mock_httpx_client):
        """Test adapter initialization with valid configuration."""
        adapter = ClickUpAdapter(valid_config)

        assert adapter.name == "clickup"
        assert adapter._api_key == "pk_test_key_123"
        assert adapter._list_id == "123456789"
        assert adapter._timeout == 10.0

        # Verify httpx client was instantiated
        mock_httpx_client.assert_called_once()

    def test_init_without_api_key(self):
        """Test adapter raises ValueError when api_key is missing."""
        config = {"list_id": "123456"}

        with pytest.raises(ValueError, match="requires 'api_key'"):
            ClickUpAdapter(config)

    def test_init_without_list_id(self):
        """Test adapter raises ValueError when list_id is missing."""
        config = {"api_key": "pk_key"}

        with pytest.raises(ValueError, match="requires 'list_id'"):
            ClickUpAdapter(config)

    def test_init_with_default_timeout(self, mock_httpx_client):
        """Test adapter uses default timeout when not specified."""
        config = {
            "api_key": "pk_key",
            "list_id": "list123",
        }

        adapter = ClickUpAdapter(config)
        assert adapter._timeout == 10.0


class TestClickUpAdapterSaveTask:
    """Tests for ClickUpAdapter.save_task() method."""

    @pytest.mark.asyncio
    async def test_save_task_success(self, valid_config, sample_task, mock_httpx_client):
        """Test successful task save to ClickUp."""
        # Setup mock response
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "cu_task_id_789"}
        mock_response.status_code = 200
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value = mock_client_instance

        adapter = ClickUpAdapter(valid_config)
        task_id = await adapter.save_task(sample_task)

        assert task_id == "cu_task_id_789"
        mock_client_instance.post.assert_called_once()

        # Verify API endpoint
        call_args = mock_client_instance.post.call_args
        assert call_args[0][0] == "/list/123456789/task"

    @pytest.mark.asyncio
    async def test_save_task_with_all_fields(self, valid_config, sample_task, mock_httpx_client):
        """Test save_task includes all task fields in payload."""
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "cu_id"}
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value = mock_client_instance

        adapter = ClickUpAdapter(valid_config)
        await adapter.save_task(sample_task)

        call_payload = mock_client_instance.post.call_args[1]["json"]

        # Verify all fields
        assert call_payload["name"] == sample_task.title
        assert call_payload["description"] == sample_task.description
        assert call_payload["status"] == "in progress"
        assert call_payload["priority"] == 3  # medium
        assert "due_date" in call_payload

    @pytest.mark.asyncio
    async def test_save_task_http_error(self, valid_config, sample_task, mock_httpx_client):
        """Test save_task raises StorageAdapterError on HTTP error."""
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_client_instance.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Unauthorized",
                request=MagicMock(),
                response=mock_response,
            )
        )
        mock_httpx_client.return_value = mock_client_instance

        adapter = ClickUpAdapter(valid_config)

        with pytest.raises(StorageAdapterError, match="ClickUp API error"):
            await adapter.save_task(sample_task)

    @pytest.mark.asyncio
    async def test_save_task_invalid_response(self, valid_config, sample_task, mock_httpx_client):
        """Test save_task raises error when response missing id."""
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "Invalid"}  # No 'id'
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value = mock_client_instance

        adapter = ClickUpAdapter(valid_config)

        with pytest.raises(StorageAdapterError, match="Invalid response from ClickUp API"):
            await adapter.save_task(sample_task)


class TestClickUpAdapterUpdateTask:
    """Tests for ClickUpAdapter.update_task() method."""

    @pytest.mark.asyncio
    async def test_update_task_success(self, valid_config, sample_task, mock_httpx_client):
        """Test successful task update in ClickUp."""
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client_instance.put = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value = mock_client_instance

        adapter = ClickUpAdapter(valid_config)
        result = await adapter.update_task("cu_task_123", sample_task)

        assert result is True
        mock_client_instance.put.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, valid_config, sample_task, mock_httpx_client):
        """Test update_task returns False when task not found."""
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client_instance.put = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Not Found",
                request=MagicMock(),
                response=mock_response,
            )
        )
        mock_httpx_client.return_value = mock_client_instance

        adapter = ClickUpAdapter(valid_config)
        result = await adapter.update_task("cu_invalid", sample_task)

        assert result is False

    @pytest.mark.asyncio
    async def test_update_task_http_error(self, valid_config, sample_task, mock_httpx_client):
        """Test update_task raises StorageAdapterError on non-404 HTTP error."""
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_client_instance.put = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Server Error",
                request=MagicMock(),
                response=mock_response,
            )
        )
        mock_httpx_client.return_value = mock_client_instance

        adapter = ClickUpAdapter(valid_config)

        with pytest.raises(StorageAdapterError, match="ClickUp API error"):
            await adapter.update_task("cu_task_123", sample_task)


class TestClickUpAdapterDeleteTask:
    """Tests for ClickUpAdapter.delete_task() method."""

    @pytest.mark.asyncio
    async def test_delete_task_success(self, valid_config, mock_httpx_client):
        """Test successful task deletion from ClickUp."""
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client_instance.delete = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value = mock_client_instance

        adapter = ClickUpAdapter(valid_config)
        result = await adapter.delete_task("cu_task_123")

        assert result is True
        mock_client_instance.delete.assert_called_once_with("/task/cu_task_123")

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, valid_config, mock_httpx_client):
        """Test delete_task returns False when task not found."""
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client_instance.delete = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Not Found",
                request=MagicMock(),
                response=mock_response,
            )
        )
        mock_httpx_client.return_value = mock_client_instance

        adapter = ClickUpAdapter(valid_config)
        result = await adapter.delete_task("cu_invalid")

        assert result is False


class TestClickUpAdapterGetTask:
    """Tests for ClickUpAdapter.get_task() method."""

    @pytest.mark.asyncio
    async def test_get_task_success(self, valid_config, mock_httpx_client):
        """Test successful task retrieval from ClickUp."""
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "cu_task_123",
            "name": "Retrieved Task",
            "description": "Task description",
            "status": {"status": "in progress"},
            "priority": 2,
            "due_date": 1738238400000,  # Timestamp in milliseconds
        }
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value = mock_client_instance

        adapter = ClickUpAdapter(valid_config)
        task = await adapter.get_task("cu_task_123")

        assert task is not None
        assert task.title == "Retrieved Task"
        assert task.description == "Task description"
        assert task.status == "in_progress"
        assert task.priority == "high"

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, valid_config, mock_httpx_client):
        """Test get_task returns None when task not found."""
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value = mock_client_instance

        adapter = ClickUpAdapter(valid_config)
        task = await adapter.get_task("cu_invalid")

        assert task is None


class TestClickUpAdapterHealthCheck:
    """Tests for ClickUpAdapter.health_check() method."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, valid_config, mock_httpx_client):
        """Test health_check returns healthy status."""
        mock_client_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_httpx_client.return_value = mock_client_instance

        adapter = ClickUpAdapter(valid_config)
        health = await adapter.health_check()

        assert health["status"] == "healthy"
        assert "latency_ms" in health
        assert "message" in health
        assert "timestamp" in health
        assert "123456789" in health["message"]

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, valid_config, mock_httpx_client):
        """Test health_check returns unhealthy on error."""
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(
            side_effect=httpx.TimeoutException("Request timeout")
        )
        mock_httpx_client.return_value = mock_client_instance

        adapter = ClickUpAdapter(valid_config)
        health = await adapter.health_check()

        assert health["status"] == "unhealthy"
        assert "latency_ms" in health
        assert "unreachable" in health["message"].lower()


class TestClickUpAdapterClose:
    """Tests for ClickUpAdapter.close() method."""

    @pytest.mark.asyncio
    async def test_close_calls_client_aclose(self, valid_config, mock_httpx_client):
        """Test close() calls httpx client aclose()."""
        mock_client_instance = AsyncMock()
        mock_client_instance.aclose = AsyncMock()
        mock_httpx_client.return_value = mock_client_instance

        adapter = ClickUpAdapter(valid_config)
        await adapter.close()

        mock_client_instance.aclose.assert_called_once()


class TestClickUpAdapterPayloadBuilder:
    """Tests for ClickUpAdapter._build_clickup_payload() private method."""

    def test_build_payload_minimal_task(self, valid_config, mock_httpx_client):
        """Test payload builder with minimal task (only title)."""
        mock_httpx_client.return_value = AsyncMock()

        adapter = ClickUpAdapter(valid_config)
        task = TaskRecord(
            id=uuid4(),
            title="Minimal ClickUp Task",
            status=TaskStatus.TODO,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        payload = adapter._build_clickup_payload(task)

        assert payload["name"] == "Minimal ClickUp Task"
        assert "status" in payload
        assert payload["status"] == "to do"

    def test_build_payload_status_mapping(self, valid_config, mock_httpx_client):
        """Test correct status mapping to ClickUp status values."""
        mock_httpx_client.return_value = AsyncMock()

        adapter = ClickUpAdapter(valid_config)

        status_mappings = {
            "pending": "to do",
            "in_progress": "in progress",
            "completed": "complete",
            "cancelled": "cancelled",
        }

        for sparkone_status, clickup_status in status_mappings.items():
            task = TaskRecord(
                id=uuid4(),
                title="Test",
                status=sparkone_status,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            payload = adapter._build_clickup_payload(task)
            assert payload["status"] == clickup_status

    def test_build_payload_priority_mapping(self, valid_config, mock_httpx_client):
        """Test correct priority mapping to ClickUp priority values."""
        mock_httpx_client.return_value = AsyncMock()

        adapter = ClickUpAdapter(valid_config)

        priority_mappings = {
            "high": 2,
            "medium": 3,
            "low": 4,
        }

        for sparkone_priority, clickup_priority in priority_mappings.items():
            task = TaskRecord(
                id=uuid4(),
                title="Test",
                status=TaskStatus.TODO,
                priority=sparkone_priority,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            payload = adapter._build_clickup_payload(task)
            assert payload["priority"] == clickup_priority

    def test_build_payload_due_date_milliseconds(self, valid_config, mock_httpx_client):
        """Test due_date is converted to milliseconds timestamp."""
        mock_httpx_client.return_value = AsyncMock()

        adapter = ClickUpAdapter(valid_config)
        due_date = datetime(2025, 3, 1, 15, 30, 0, tzinfo=timezone.utc)

        task = TaskRecord(
            id=uuid4(),
            title="Test",
            status=TaskStatus.TODO,
            due_date=due_date,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        payload = adapter._build_clickup_payload(task)
        expected_timestamp = int(due_date.timestamp() * 1000)

        assert payload["due_date"] == expected_timestamp


class TestClickUpAdapterTaskParser:
    """Tests for ClickUpAdapter._parse_clickup_task() private method."""

    def test_parse_clickup_task_complete(self, valid_config, mock_httpx_client):
        """Test parsing complete ClickUp task response."""
        mock_httpx_client.return_value = AsyncMock()

        adapter = ClickUpAdapter(valid_config)
        clickup_data = {
            "id": "cu_parsed_123",
            "name": "Parsed Task",
            "description": "Description here",
            "status": {"status": "in progress"},
            "priority": 2,
            "due_date": 1740834600000,  # Feb 29, 2025
        }

        task = adapter._parse_clickup_task(clickup_data)

        assert task.title == "Parsed Task"
        assert task.description == "Description here"
        assert task.status == "in_progress"
        assert task.priority == "high"
        assert task.external_id == "cu_parsed_123"
        assert task.channel == "clickup"
        assert task.sender == "clickup_sync"

    def test_parse_clickup_task_minimal(self, valid_config, mock_httpx_client):
        """Test parsing minimal ClickUp task (only required fields)."""
        mock_httpx_client.return_value = AsyncMock()

        adapter = ClickUpAdapter(valid_config)
        clickup_data = {
            "id": "cu_minimal",
            "name": "Minimal Task",
        }

        task = adapter._parse_clickup_task(clickup_data)

        assert task.title == "Minimal Task"
        assert task.status == "pending"  # default
        assert task.priority == "medium"  # default


__all__ = [
    "TestClickUpAdapterInitialization",
    "TestClickUpAdapterSaveTask",
    "TestClickUpAdapterUpdateTask",
    "TestClickUpAdapterDeleteTask",
    "TestClickUpAdapterGetTask",
    "TestClickUpAdapterHealthCheck",
    "TestClickUpAdapterClose",
    "TestClickUpAdapterPayloadBuilder",
    "TestClickUpAdapterTaskParser",
]
