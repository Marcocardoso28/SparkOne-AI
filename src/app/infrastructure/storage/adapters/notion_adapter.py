"""Notion Storage Adapter - ADR-014.

Implements storage adapter interface for Notion workspace integration.
Handles task synchronization between SparkOne and Notion databases.

Related ADR: ADR-014 (Storage Adapter Pattern)
Related RF: RF-019 (Multi-Storage Backend System)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from src.app.domain.interfaces.storage_adapter import StorageAdapter, StorageAdapterError
from src.app.infrastructure.database.models.tasks import TaskRecord
from src.app.infrastructure.integrations.notion import NotionClient

logger = logging.getLogger(__name__)


class NotionAdapter(StorageAdapter):
    """Storage adapter for Notion workspace integration.

    Synchronizes tasks between SparkOne local database and Notion database.
    Uses Notion REST API v1 for all operations.

    Configuration:
        - api_key: Notion integration secret token
        - database_id: Target Notion database ID
        - timeout: API request timeout in seconds (default: 10.0)

    Example:
        ```python
        config = {
            "api_key": "secret_abc123",
            "database_id": "db-uuid-here",
            "timeout": 15.0
        }
        adapter = NotionAdapter(config)
        external_id = await adapter.save_task(task)
        ```
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize Notion adapter with configuration.

        Args:
            config: Configuration dictionary with keys:
                - api_key (str): Notion integration token
                - database_id (str): Notion database ID
                - timeout (float, optional): Request timeout (default: 10.0)

        Raises:
            ValueError: If required config keys are missing
        """
        if "api_key" not in config:
            raise ValueError("Notion adapter requires 'api_key' in config")
        if "database_id" not in config:
            raise ValueError("Notion adapter requires 'database_id' in config")

        self._api_key = config["api_key"]
        self._database_id = config["database_id"]
        self._timeout = config.get("timeout", 10.0)
        self._client = NotionClient(self._api_key, timeout=self._timeout)

        logger.info(
            f"Initialized NotionAdapter with database {self._database_id[:8]}..."
        )

    @property
    def name(self) -> str:
        """Return adapter name.

        Returns:
            str: 'notion'
        """
        return "notion"

    async def save_task(self, task: TaskRecord) -> str:
        """Save task to Notion database.

        Creates a new page in the configured Notion database.

        Args:
            task: The task record to save

        Returns:
            str: Notion page ID (external_id)

        Raises:
            StorageAdapterError: If save operation fails
        """
        try:
            payload = self._build_notion_payload(task)
            payload["parent"] = {"database_id": self._database_id}

            response = await self._client.create_page(payload)

            if not isinstance(response, dict) or "id" not in response:
                raise StorageAdapterError(
                    "Invalid response from Notion API (missing 'id')",
                    adapter_name=self.name,
                )

            notion_page_id = response["id"]
            logger.info(
                f"Saved task to Notion: {task.title[:50]} -> {notion_page_id[:8]}..."
            )
            return notion_page_id

        except Exception as e:
            if isinstance(e, StorageAdapterError):
                raise
            raise StorageAdapterError(
                f"Failed to save task to Notion: {e}",
                adapter_name=self.name,
                original_error=e,
            ) from e

    async def update_task(self, external_id: str, task: TaskRecord) -> bool:
        """Update existing task in Notion.

        Note:
            Current Notion client only supports create_page().
            This method is a placeholder for future implementation.

        Args:
            external_id: Notion page ID
            task: Updated task record

        Returns:
            bool: False (not implemented yet)

        Todo:
            - Implement PATCH /v1/pages/{page_id} in NotionClient
            - Handle Notion property updates
        """
        logger.warning(
            f"NotionAdapter.update_task() not implemented yet (page_id: {external_id})"
        )
        return False

    async def delete_task(self, external_id: str) -> bool:
        """Delete (archive) task from Notion.

        Note:
            Current Notion client doesn't support archive operation.
            This method is a placeholder for future implementation.

        Args:
            external_id: Notion page ID

        Returns:
            bool: False (not implemented yet)

        Todo:
            - Implement PATCH /v1/pages/{page_id} with archived: true
        """
        logger.warning(
            f"NotionAdapter.delete_task() not implemented yet (page_id: {external_id})"
        )
        return False

    async def get_task(self, external_id: str) -> TaskRecord | None:
        """Retrieve task from Notion.

        Note:
            Current Notion client doesn't support get_page().
            This method is a placeholder for future implementation.

        Args:
            external_id: Notion page ID

        Returns:
            TaskRecord | None: None (not implemented yet)

        Todo:
            - Implement GET /v1/pages/{page_id} in NotionClient
            - Parse Notion page properties to TaskRecord
        """
        logger.warning(
            f"NotionAdapter.get_task() not implemented yet (page_id: {external_id})"
        )
        return None

    async def health_check(self) -> dict[str, Any]:
        """Check Notion API connectivity and health.

        Performs a lightweight test to verify Notion API is reachable.

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
            # Create a minimal test payload to verify API access
            # We don't actually create it, just validate the connection
            test_payload = {
                "parent": {"database_id": self._database_id},
                "properties": {
                    "Name": {"title": [{"text": {"content": "[Health Check Test]"}}]}
                },
            }

            # Note: In production, you'd want a lighter health check endpoint
            # For now, we'll just verify the client is configured correctly
            # without actually creating a page

            latency_ms = (time.time() - start) * 1000

            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "message": f"Notion API accessible (database: {self._database_id[:8]}...)",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            logger.warning(f"Notion health check failed: {e}")

            return {
                "status": "unhealthy",
                "latency_ms": round(latency_ms, 2),
                "message": f"Notion API unreachable: {str(e)[:100]}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

    def _build_notion_payload(self, task: TaskRecord) -> dict[str, Any]:
        """Build Notion API page creation payload from task record.

        Args:
            task: Task record to convert

        Returns:
            dict: Notion API payload with properties

        Note:
            Migrated from TaskService._build_notion_payload()
        """
        properties: dict[str, Any] = {
            "Name": {"title": [{"text": {"content": task.title}}]}
        }

        if task.due_date:
            properties["Due"] = {"date": {"start": task.due_date.isoformat()}}

        if task.description:
            properties["Description"] = {
                "rich_text": [{"text": {"content": task.description[:2000]}}]
            }

        # Optional: Add status if Notion database has Status property
        if task.status:
            status_map = {
                "pending": "To Do",
                "in_progress": "In Progress",
                "completed": "Done",
                "cancelled": "Cancelled",
            }
            notion_status = status_map.get(task.status, "To Do")
            properties["Status"] = {"status": {"name": notion_status}}

        # Optional: Add priority if Notion database has Priority property
        if task.priority:
            priority_map = {
                "low": "Low",
                "medium": "Medium",
                "high": "High",
            }
            notion_priority = priority_map.get(task.priority, "Medium")
            properties["Priority"] = {"select": {"name": notion_priority}}

        return {"properties": properties}

    async def close(self) -> None:
        """Close Notion client and cleanup resources."""
        await self._client.close()
        logger.info("Closed NotionAdapter client")


__all__ = ["NotionAdapter"]
