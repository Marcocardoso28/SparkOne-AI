"""ClickUp Storage Adapter - ADR-014.

Implements storage adapter interface for ClickUp workspace integration.
Handles task synchronization between SparkOne and ClickUp lists.

Related ADR: ADR-014 (Storage Adapter Pattern)
Related RF: RF-019 (Multi-Storage Backend System)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.domain.interfaces.storage_adapter import StorageAdapter, StorageAdapterError
from app.infrastructure.database.models.tasks import TaskRecord

logger = logging.getLogger(__name__)


class ClickUpAdapter(StorageAdapter):
    """Storage adapter for ClickUp workspace integration.

    Synchronizes tasks between SparkOne local database and ClickUp lists.
    Uses ClickUp API v2 for all operations.

    Configuration:
        - api_key: ClickUp personal API token
        - list_id: Target ClickUp list ID
        - timeout: API request timeout in seconds (default: 10.0)

    Example:
        ```python
        config = {
            "api_key": "pk_abc123",
            "list_id": "12345678",
            "timeout": 15.0
        }
        adapter = ClickUpAdapter(config)
        task_id = await adapter.save_task(task)
        ```

    API Docs: https://clickup.com/api
    """

    BASE_URL = "https://api.clickup.com/api/v2"

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize ClickUp adapter with configuration.

        Args:
            config: Configuration dictionary with keys:
                - api_key (str): ClickUp API token
                - list_id (str): ClickUp list ID
                - timeout (float, optional): Request timeout (default: 10.0)

        Raises:
            ValueError: If required config keys are missing
        """
        if "api_key" not in config:
            raise ValueError("ClickUp adapter requires 'api_key' in config")
        if "list_id" not in config:
            raise ValueError("ClickUp adapter requires 'list_id' in config")

        self._api_key = config["api_key"]
        self._list_id = config["list_id"]
        self._timeout = config.get("timeout", 10.0)

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=self._timeout,
            headers={
                "Authorization": self._api_key,
                "Content-Type": "application/json",
            },
        )

        logger.info(f"Initialized ClickUpAdapter with list {self._list_id}")

    @property
    def name(self) -> str:
        """Return adapter name.

        Returns:
            str: 'clickup'
        """
        return "clickup"

    async def save_task(self, task: TaskRecord) -> str:
        """Save task to ClickUp list.

        Creates a new task in the configured ClickUp list.

        Args:
            task: The task record to save

        Returns:
            str: ClickUp task ID (external_id)

        Raises:
            StorageAdapterError: If save operation fails

        Example:
            >>> task = TaskRecord(title="Buy groceries", status="pending")
            >>> task_id = await adapter.save_task(task)
            >>> print(task_id)
            'cu_abc123xyz'
        """
        try:
            payload = self._build_clickup_payload(task)
            url = f"/list/{self._list_id}/task"

            response = await self._client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            task_id = data.get("id")

            if not task_id:
                raise StorageAdapterError(
                    "Invalid response from ClickUp API (missing 'id')",
                    adapter_name=self.name,
                )

            logger.info(
                f"Saved task to ClickUp: {task.title[:50]} -> {task_id}"
            )
            return task_id

        except httpx.HTTPStatusError as e:
            raise StorageAdapterError(
                f"ClickUp API error ({e.response.status_code}): {e.response.text}",
                adapter_name=self.name,
                original_error=e,
            ) from e
        except Exception as e:
            if isinstance(e, StorageAdapterError):
                raise
            raise StorageAdapterError(
                f"Failed to save task to ClickUp: {e}",
                adapter_name=self.name,
                original_error=e,
            ) from e

    async def update_task(self, external_id: str, task: TaskRecord) -> bool:
        """Update existing task in ClickUp.

        Updates task properties in ClickUp list.

        Args:
            external_id: ClickUp task ID
            task: Updated task record

        Returns:
            bool: True if update succeeded

        Raises:
            StorageAdapterError: If update operation fails

        Example:
            >>> updated = await adapter.update_task("cu_abc123", task)
            >>> assert updated is True
        """
        try:
            payload = self._build_clickup_payload(task)
            url = f"/task/{external_id}"

            response = await self._client.put(url, json=payload)
            response.raise_for_status()

            logger.info(f"Updated ClickUp task: {external_id}")
            return True

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"ClickUp task not found: {external_id}")
                return False

            raise StorageAdapterError(
                f"ClickUp API error ({e.response.status_code}): {e.response.text}",
                adapter_name=self.name,
                original_error=e,
            ) from e
        except Exception as e:
            if isinstance(e, StorageAdapterError):
                raise
            raise StorageAdapterError(
                f"Failed to update ClickUp task: {e}",
                adapter_name=self.name,
                original_error=e,
            ) from e

    async def delete_task(self, external_id: str) -> bool:
        """Delete task from ClickUp.

        Permanently deletes the task from ClickUp list.

        Args:
            external_id: ClickUp task ID

        Returns:
            bool: True if deletion succeeded, False if not found

        Raises:
            StorageAdapterError: If delete operation fails

        Example:
            >>> deleted = await adapter.delete_task("cu_abc123")
            >>> assert deleted is True
        """
        try:
            url = f"/task/{external_id}"

            response = await self._client.delete(url)
            response.raise_for_status()

            logger.info(f"Deleted ClickUp task: {external_id}")
            return True

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"ClickUp task not found: {external_id}")
                return False

            raise StorageAdapterError(
                f"ClickUp API error ({e.response.status_code}): {e.response.text}",
                adapter_name=self.name,
                original_error=e,
            ) from e
        except Exception as e:
            if isinstance(e, StorageAdapterError):
                raise
            raise StorageAdapterError(
                f"Failed to delete ClickUp task: {e}",
                adapter_name=self.name,
                original_error=e,
            ) from e

    async def get_task(self, external_id: str) -> TaskRecord | None:
        """Retrieve task from ClickUp.

        Fetches task details from ClickUp and converts to TaskRecord.

        Args:
            external_id: ClickUp task ID

        Returns:
            TaskRecord | None: The task record if found, None otherwise

        Raises:
            StorageAdapterError: If retrieval operation fails

        Example:
            >>> task = await adapter.get_task("cu_abc123")
            >>> if task:
            >>>     print(task.title)
        """
        try:
            url = f"/task/{external_id}"

            response = await self._client.get(url)

            if response.status_code == 404:
                logger.warning(f"ClickUp task not found: {external_id}")
                return None

            response.raise_for_status()
            data = response.json()

            # Parse ClickUp task to TaskRecord
            task = self._parse_clickup_task(data)
            logger.info(f"Retrieved ClickUp task: {external_id}")
            return task

        except httpx.HTTPStatusError as e:
            raise StorageAdapterError(
                f"ClickUp API error ({e.response.status_code}): {e.response.text}",
                adapter_name=self.name,
                original_error=e,
            ) from e
        except Exception as e:
            if isinstance(e, StorageAdapterError):
                raise
            raise StorageAdapterError(
                f"Failed to retrieve ClickUp task: {e}",
                adapter_name=self.name,
                original_error=e,
            ) from e

    async def health_check(self) -> dict[str, Any]:
        """Check ClickUp API connectivity and health.

        Performs a lightweight test to verify ClickUp API is reachable.

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
            # Get list info to verify access
            url = f"/list/{self._list_id}"
            response = await self._client.get(url)
            response.raise_for_status()

            latency_ms = (time.time() - start) * 1000

            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "message": f"ClickUp API accessible (list: {self._list_id})",
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            }

        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            logger.warning(f"ClickUp health check failed: {e}")

            return {
                "status": "unhealthy",
                "latency_ms": round(latency_ms, 2),
                "message": f"ClickUp API unreachable: {str(e)[:100]}",
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            }

    def _build_clickup_payload(self, task: TaskRecord) -> dict[str, Any]:
        """Build ClickUp API task creation/update payload from task record.

        Args:
            task: Task record to convert

        Returns:
            dict: ClickUp API payload

        ClickUp API Reference:
            https://clickup.com/api/clickupreference/operation/CreateTask/
        """
        payload: dict[str, Any] = {
            "name": task.title,
        }

        if task.description:
            payload["description"] = task.description

        # Convert status to ClickUp format
        if task.status:
            status_map = {
                "pending": "to do",
                "in_progress": "in progress",
                "completed": "complete",
                "cancelled": "cancelled",
            }
            payload["status"] = status_map.get(task.status, "to do")

        # Add due date in milliseconds timestamp
        if task.due_date:
            payload["due_date"] = int(task.due_date.timestamp() * 1000)

        # Add priority (ClickUp uses 1=urgent, 2=high, 3=normal, 4=low)
        if task.priority:
            priority_map = {
                "high": 2,
                "medium": 3,
                "low": 4,
            }
            payload["priority"] = priority_map.get(task.priority, 3)

        return payload

    def _parse_clickup_task(self, data: dict[str, Any]) -> TaskRecord:
        """Parse ClickUp API response to TaskRecord.

        Args:
            data: ClickUp task data from API

        Returns:
            TaskRecord: Parsed task record
        """
        # Convert ClickUp status to SparkOne format
        status_map = {
            "to do": "pending",
            "in progress": "in_progress",
            "complete": "completed",
            "cancelled": "cancelled",
        }
        status = status_map.get(data.get("status", {}).get("status", "").lower(), "pending")

        # Convert priority
        priority_map = {
            1: "high",  # urgent
            2: "high",
            3: "medium",
            4: "low",
        }
        priority_value = data.get("priority")
        priority = priority_map.get(priority_value) if priority_value else "medium"

        # Parse due date (ClickUp uses milliseconds timestamp)
        due_date = None
        if data.get("due_date"):
            try:
                due_date = datetime.fromtimestamp(int(data["due_date"]) / 1000)
            except (ValueError, TypeError):
                pass

        return TaskRecord(
            title=data.get("name", ""),
            description=data.get("description"),
            status=status,
            priority=priority,
            due_date=due_date,
            channel="clickup",
            sender="clickup_sync",
            external_id=data.get("id"),
        )

    async def close(self) -> None:
        """Close ClickUp client and cleanup resources."""
        await self._client.aclose()
        logger.info("Closed ClickUpAdapter client")


__all__ = ["ClickUpAdapter"]
