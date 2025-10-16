"""Storage Adapter Interface - ADR-014.

This module defines the abstract interface that all storage backends must implement.
Enables multi-backend support (Notion, ClickUp, Google Sheets, etc.) without tight coupling.

Related ADR: ADR-014 (Storage Adapter Pattern)
Related RF: RF-019 (Multi-Storage Backend System)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.app.infrastructure.database.models.tasks import TaskRecord


class StorageAdapter(ABC):
    """Abstract base class for storage backend adapters.

    All storage adapters (Notion, ClickUp, Sheets) must implement this interface.
    Provides consistent API for CRUD operations and health monitoring.

    Example:
        ```python
        class NotionAdapter(StorageAdapter):
            @property
            def name(self) -> str:
                return "notion"

            async def save_task(self, task: TaskRecord) -> str:
                # Implementation...
                return notion_page_id
        ```
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique identifier for this adapter.

        Returns:
            str: Lowercase adapter name (e.g., 'notion', 'clickup', 'sheets')

        Example:
            >>> adapter.name
            'notion'
        """
        ...

    @abstractmethod
    async def save_task(self, task: TaskRecord) -> str:
        """Save a new task to the external storage backend.

        Args:
            task: The task record to save

        Returns:
            str: External ID assigned by the backend (e.g., Notion page ID)

        Raises:
            StorageAdapterError: If save operation fails after retries

        Example:
            >>> task = TaskRecord(title="Buy groceries", status="pending")
            >>> external_id = await adapter.save_task(task)
            >>> print(external_id)
            'abc123-notion-page-id'
        """
        ...

    @abstractmethod
    async def update_task(self, external_id: str, task: TaskRecord) -> bool:
        """Update an existing task in the external storage backend.

        Args:
            external_id: The external ID returned from save_task()
            task: Updated task record

        Returns:
            bool: True if update succeeded, False otherwise

        Raises:
            StorageAdapterError: If update operation fails critically

        Example:
            >>> success = await adapter.update_task("abc123", updated_task)
            >>> assert success is True
        """
        ...

    @abstractmethod
    async def delete_task(self, external_id: str) -> bool:
        """Delete a task from the external storage backend.

        Args:
            external_id: The external ID of the task to delete

        Returns:
            bool: True if deletion succeeded, False if task not found

        Raises:
            StorageAdapterError: If delete operation fails critically

        Example:
            >>> deleted = await adapter.delete_task("abc123")
            >>> assert deleted is True
        """
        ...

    @abstractmethod
    async def get_task(self, external_id: str) -> TaskRecord | None:
        """Retrieve a task from the external storage backend.

        Args:
            external_id: The external ID of the task to retrieve

        Returns:
            TaskRecord | None: The task record if found, None otherwise

        Raises:
            StorageAdapterError: If retrieval operation fails critically

        Example:
            >>> task = await adapter.get_task("abc123")
            >>> if task:
            >>>     print(task.title)
        """
        ...

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Check the health and connectivity of the storage backend.

        Returns:
            dict: Health status including:
                - status: 'healthy' | 'degraded' | 'unhealthy'
                - latency_ms: Round-trip latency in milliseconds
                - message: Human-readable status message
                - timestamp: ISO timestamp of check

        Example:
            >>> health = await adapter.health_check()
            >>> print(health)
            {
                'status': 'healthy',
                'latency_ms': 245,
                'message': 'Notion API responding normally',
                'timestamp': '2025-01-27T14:30:00Z'
            }
        """
        ...

    async def supports_batch_operations(self) -> bool:
        """Indicate if this adapter supports batch operations.

        Returns:
            bool: True if batch save/update/delete are supported

        Note:
            Default implementation returns False.
            Override to return True and implement batch methods.
        """
        return False

    async def batch_save_tasks(self, tasks: list[TaskRecord]) -> list[str]:
        """Save multiple tasks in a single batch operation.

        Args:
            tasks: List of task records to save

        Returns:
            list[str]: List of external IDs in same order as input

        Raises:
            NotImplementedError: If adapter doesn't support batch operations

        Note:
            Only implement if supports_batch_operations() returns True
        """
        raise NotImplementedError(
            f"{self.name} adapter does not support batch operations"
        )


class StorageAdapterError(Exception):
    """Base exception for storage adapter errors.

    Used to wrap backend-specific exceptions with consistent error handling.
    """

    def __init__(
        self,
        message: str,
        adapter_name: str,
        original_error: Exception | None = None,
    ) -> None:
        """Initialize storage adapter error.

        Args:
            message: Human-readable error description
            adapter_name: Name of the adapter that raised the error
            original_error: Original exception from the backend API
        """
        self.adapter_name = adapter_name
        self.original_error = original_error
        super().__init__(f"[{adapter_name}] {message}")


__all__ = ["StorageAdapter", "StorageAdapterError"]
