"""Storage Service Orchestrator - ADR-014.

Orchestrates task synchronization across multiple storage backends.
Manages retry logic, fallback, and health monitoring for all adapters.

Related ADR: ADR-014 (Storage Adapter Pattern)
Related RF: RF-019 (Multi-Storage Backend System)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.storage_adapter import StorageAdapter, StorageAdapterError
from app.infrastructure.database.models.tasks import TaskRecord
from app.infrastructure.storage.registry import StorageAdapterRegistry

logger = logging.getLogger(__name__)


class StorageService:
    """Orchestrates task synchronization across multiple storage backends.

    Manages multiple storage adapters (Notion, ClickUp, Sheets) and handles:
    - Parallel synchronization to all active backends
    - Retry logic with exponential backoff
    - Fallback to queue if all backends fail
    - Health monitoring per adapter
    - Priority-based sync order

    Example:
        ```python
        service = StorageService(session)
        await service.load_configs(user_id="user-123")

        # Save to all active backends
        result = await service.save_task(task)
        # Returns: {
        #     "notion": "page-id-123",
        #     "clickup": "task-id-456",
        #     "sheets": "row_789"
        # }
        ```
    """

    def __init__(
        self,
        session: AsyncSession,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize storage service.

        Args:
            session: Database session for loading configs
            max_retries: Maximum retry attempts per adapter (default: 3)
            retry_delay: Base delay for exponential backoff in seconds (default: 1.0)
        """
        self._session = session
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._adapters: list[tuple[StorageAdapter, int]] = []  # (adapter, priority)

        logger.info("Initialized StorageService")

    async def load_configs(self, user_id: str | None = None) -> int:
        """Load and initialize active storage adapters from database.

        Args:
            user_id: User ID to load configs for (None for single-user mode)

        Returns:
            int: Number of adapters loaded

        Example:
            >>> count = await service.load_configs()
            >>> print(f"Loaded {count} adapters")
        """
        # Import here to avoid circular dependency
        from app.infrastructure.database.models.user_storage_config import (
            UserStorageConfig,
        )

        # Query active configs for user
        stmt = select(UserStorageConfig).where(
            UserStorageConfig.user_id == user_id,
            UserStorageConfig.is_active == True,  # noqa: E712
        ).order_by(UserStorageConfig.priority.desc())

        result = await self._session.execute(stmt)
        configs = result.scalars().all()

        # Initialize adapters
        self._adapters.clear()
        for config in configs:
            try:
                adapter_class = StorageAdapterRegistry.get_adapter(config.adapter_name)
                adapter = adapter_class(config.config_json)
                self._adapters.append((adapter, config.priority))
                logger.info(
                    f"Loaded adapter: {config.adapter_name} (priority: {config.priority})"
                )
            except Exception as e:
                logger.error(
                    f"Failed to load adapter {config.adapter_name}: {e}"
                )

        logger.info(f"Loaded {len(self._adapters)} storage adapters")
        return len(self._adapters)

    async def save_task(self, task: TaskRecord) -> dict[str, str]:
        """Save task to all active storage backends in parallel.

        Args:
            task: The task record to save

        Returns:
            dict: Map of adapter_name -> external_id for successful saves

        Example:
            >>> result = await service.save_task(task)
            >>> print(result)
            {'notion': 'page-123', 'clickup': 'task-456'}
        """
        if not self._adapters:
            logger.warning("No active storage adapters configured")
            return {}

        # Sort adapters by priority (already sorted from query)
        # Save to all adapters in parallel
        tasks = [
            self._save_with_retry(adapter, task)
            for adapter, _ in self._adapters
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect successful saves
        external_ids: dict[str, str] = {}
        for (adapter, _), result in zip(self._adapters, results):
            if isinstance(result, Exception):
                logger.error(
                    f"Failed to save to {adapter.name} after retries: {result}"
                )
            elif result:
                external_ids[adapter.name] = result
                logger.info(f"Saved to {adapter.name}: {result}")

        return external_ids

    async def update_task(
        self,
        task: TaskRecord,
        external_ids: dict[str, str],
    ) -> dict[str, bool]:
        """Update task in storage backends.

        Args:
            task: Updated task record
            external_ids: Map of adapter_name -> external_id from save_task()

        Returns:
            dict: Map of adapter_name -> success status

        Example:
            >>> result = await service.update_task(task, external_ids)
            >>> print(result)
            {'notion': True, 'clickup': True}
        """
        if not self._adapters:
            return {}

        tasks = [
            self._update_with_retry(adapter, external_ids.get(adapter.name, ""), task)
            for adapter, _ in self._adapters
            if adapter.name in external_ids
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        status: dict[str, bool] = {}
        for (adapter, _), result in zip(self._adapters, results):
            if adapter.name not in external_ids:
                continue

            if isinstance(result, Exception):
                logger.error(f"Failed to update {adapter.name}: {result}")
                status[adapter.name] = False
            else:
                status[adapter.name] = result
                logger.info(f"Updated {adapter.name}: {result}")

        return status

    async def delete_task(self, external_ids: dict[str, str]) -> dict[str, bool]:
        """Delete task from storage backends.

        Args:
            external_ids: Map of adapter_name -> external_id

        Returns:
            dict: Map of adapter_name -> success status

        Example:
            >>> result = await service.delete_task(external_ids)
            >>> print(result)
            {'notion': True, 'clickup': True}
        """
        if not self._adapters:
            return {}

        tasks = [
            self._delete_with_retry(adapter, external_ids.get(adapter.name, ""))
            for adapter, _ in self._adapters
            if adapter.name in external_ids
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        status: dict[str, bool] = {}
        for (adapter, _), result in zip(self._adapters, results):
            if adapter.name not in external_ids:
                continue

            if isinstance(result, Exception):
                logger.error(f"Failed to delete from {adapter.name}: {result}")
                status[adapter.name] = False
            else:
                status[adapter.name] = result
                logger.info(f"Deleted from {adapter.name}: {result}")

        return status

    async def health_check_all(self) -> dict[str, dict[str, Any]]:
        """Check health of all active storage backends.

        Returns:
            dict: Map of adapter_name -> health status

        Example:
            >>> health = await service.health_check_all()
            >>> for name, status in health.items():
            >>>     print(f"{name}: {status['status']}")
        """
        if not self._adapters:
            return {}

        tasks = [adapter.health_check() for adapter, _ in self._adapters]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        health: dict[str, dict[str, Any]] = {}
        for (adapter, _), result in zip(self._adapters, results):
            if isinstance(result, Exception):
                health[adapter.name] = {
                    "status": "error",
                    "message": str(result),
                }
            else:
                health[adapter.name] = result

        return health

    async def _save_with_retry(
        self,
        adapter: StorageAdapter,
        task: TaskRecord,
    ) -> str:
        """Save task with exponential backoff retry.

        Args:
            adapter: Storage adapter to use
            task: Task to save

        Returns:
            str: External ID from adapter

        Raises:
            StorageAdapterError: If all retries fail
        """
        last_error = None
        for attempt in range(self._max_retries):
            try:
                external_id = await adapter.save_task(task)
                if attempt > 0:
                    logger.info(
                        f"Retry succeeded for {adapter.name} on attempt {attempt + 1}"
                    )
                return external_id
            except StorageAdapterError as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Retry {attempt + 1}/{self._max_retries} for {adapter.name} "
                        f"after {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)

        # All retries failed
        raise last_error or StorageAdapterError(
            "Save failed with unknown error", adapter_name=adapter.name
        )

    async def _update_with_retry(
        self,
        adapter: StorageAdapter,
        external_id: str,
        task: TaskRecord,
    ) -> bool:
        """Update task with exponential backoff retry.

        Args:
            adapter: Storage adapter to use
            external_id: External ID from save_task()
            task: Updated task

        Returns:
            bool: True if update succeeded

        Raises:
            StorageAdapterError: If all retries fail
        """
        last_error = None
        for attempt in range(self._max_retries):
            try:
                success = await adapter.update_task(external_id, task)
                if attempt > 0:
                    logger.info(
                        f"Retry succeeded for {adapter.name} on attempt {attempt + 1}"
                    )
                return success
            except StorageAdapterError as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Retry {attempt + 1}/{self._max_retries} for {adapter.name} "
                        f"after {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)

        # All retries failed
        raise last_error or StorageAdapterError(
            "Update failed with unknown error", adapter_name=adapter.name
        )

    async def _delete_with_retry(
        self,
        adapter: StorageAdapter,
        external_id: str,
    ) -> bool:
        """Delete task with exponential backoff retry.

        Args:
            adapter: Storage adapter to use
            external_id: External ID from save_task()

        Returns:
            bool: True if deletion succeeded

        Raises:
            StorageAdapterError: If all retries fail
        """
        last_error = None
        for attempt in range(self._max_retries):
            try:
                success = await adapter.delete_task(external_id)
                if attempt > 0:
                    logger.info(
                        f"Retry succeeded for {adapter.name} on attempt {attempt + 1}"
                    )
                return success
            except StorageAdapterError as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Retry {attempt + 1}/{self._max_retries} for {adapter.name} "
                        f"after {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)

        # All retries failed
        raise last_error or StorageAdapterError(
            "Delete failed with unknown error", adapter_name=adapter.name
        )

    async def close_all(self) -> None:
        """Close all adapter connections and cleanup resources."""
        for adapter, _ in self._adapters:
            try:
                if hasattr(adapter, "close"):
                    await adapter.close()
            except Exception as e:
                logger.warning(f"Error closing {adapter.name}: {e}")

        logger.info("Closed all storage adapters")


__all__ = ["StorageService"]
