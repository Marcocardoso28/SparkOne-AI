"""Storage Adapter Registry - ADR-014.

Provides centralized registry for storage adapter discovery and instantiation.
Implements singleton pattern to ensure single source of truth for available adapters.

Related ADR: ADR-014 (Storage Adapter Pattern)
Related RF: RF-019 (Multi-Storage Backend System)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.app.domain.interfaces.storage_adapter import StorageAdapter

logger = logging.getLogger(__name__)


class StorageAdapterRegistry:
    """Centralized registry for storage backend adapters.

    Implements singleton pattern with auto-discovery capabilities.
    Manages registration, retrieval, and listing of available storage adapters.

    Example:
        ```python
        # Register adapters
        registry = StorageAdapterRegistry()
        registry.register(NotionAdapter)
        registry.register(ClickUpAdapter)

        # Get specific adapter
        adapter_class = registry.get_adapter("notion")
        adapter = adapter_class(config)

        # List all available
        available = registry.list_available()
        # Returns: ['notion', 'clickup', 'sheets']
        ```
    """

    _instance: StorageAdapterRegistry | None = None
    _adapters: dict[str, type[StorageAdapter]] = {}

    def __new__(cls) -> StorageAdapterRegistry:
        """Ensure only one registry instance exists (Singleton pattern).

        Returns:
            StorageAdapterRegistry: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.info("Initialized StorageAdapterRegistry singleton")
        return cls._instance

    @classmethod
    def register(cls, adapter_class: type[StorageAdapter]) -> None:
        """Register a storage adapter class.

        Args:
            adapter_class: The adapter class to register (not an instance)

        Raises:
            TypeError: If adapter_class doesn't inherit from StorageAdapter
            ValueError: If an adapter with the same name is already registered

        Example:
            >>> StorageAdapterRegistry.register(NotionAdapter)
            >>> StorageAdapterRegistry.register(ClickUpAdapter)
        """
        from src.app.domain.interfaces.storage_adapter import StorageAdapter

        if not issubclass(adapter_class, StorageAdapter):
            raise TypeError(
                f"{adapter_class.__name__} must inherit from StorageAdapter"
            )

        # Get adapter name by instantiating temporarily
        # (We need the name property which is abstract)
        try:
            temp_instance = adapter_class.__new__(adapter_class)
            adapter_name = adapter_class.name.fget(temp_instance)  # type: ignore
        except Exception as e:
            raise ValueError(
                f"Cannot determine adapter name for {adapter_class.__name__}: {e}"
            ) from e

        if adapter_name in cls._adapters:
            existing_class = cls._adapters[adapter_name]
            if existing_class != adapter_class:
                logger.warning(
                    f"Adapter '{adapter_name}' already registered with "
                    f"{existing_class.__name__}, replacing with {adapter_class.__name__}"
                )

        cls._adapters[adapter_name] = adapter_class
        logger.info(f"Registered storage adapter: {adapter_name} ({adapter_class.__name__})")

    @classmethod
    def get_adapter(cls, name: str) -> type[StorageAdapter]:
        """Retrieve an adapter class by name.

        Args:
            name: The adapter name (e.g., 'notion', 'clickup')

        Returns:
            type[StorageAdapter]: The adapter class

        Raises:
            KeyError: If no adapter with the given name is registered

        Example:
            >>> adapter_class = StorageAdapterRegistry.get_adapter("notion")
            >>> adapter = adapter_class(config)
            >>> await adapter.save_task(task)
        """
        if name not in cls._adapters:
            available = ", ".join(cls._adapters.keys()) or "none"
            raise KeyError(
                f"No adapter registered with name '{name}'. "
                f"Available adapters: {available}"
            )
        return cls._adapters[name]

    @classmethod
    def list_available(cls) -> list[str]:
        """List all registered adapter names.

        Returns:
            list[str]: Sorted list of registered adapter names

        Example:
            >>> adapters = StorageAdapterRegistry.list_available()
            >>> print(adapters)
            ['clickup', 'notion', 'sheets']
        """
        return sorted(cls._adapters.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if an adapter with the given name is registered.

        Args:
            name: The adapter name to check

        Returns:
            bool: True if registered, False otherwise

        Example:
            >>> if StorageAdapterRegistry.is_registered("notion"):
            >>>     adapter = StorageAdapterRegistry.get_adapter("notion")
        """
        return name in cls._adapters

    @classmethod
    def clear(cls) -> None:
        """Clear all registered adapters.

        Warning:
            Only use this in tests! This will remove all registered adapters.

        Example:
            >>> # In tests
            >>> StorageAdapterRegistry.clear()
            >>> assert StorageAdapterRegistry.list_available() == []
        """
        cls._adapters.clear()
        logger.warning("Cleared all registered storage adapters")

    @classmethod
    def get_adapter_info(cls, name: str) -> dict[str, Any]:
        """Get detailed information about a registered adapter.

        Args:
            name: The adapter name

        Returns:
            dict: Adapter information including:
                - name: Adapter name
                - class: Class name
                - module: Module path
                - supports_batch: Whether batch operations are supported

        Raises:
            KeyError: If adapter not found

        Example:
            >>> info = StorageAdapterRegistry.get_adapter_info("notion")
            >>> print(info)
            {
                'name': 'notion',
                'class': 'NotionAdapter',
                'module': 'src.app.infrastructure.storage.adapters.notion_adapter',
                'supports_batch': False
            }
        """
        adapter_class = cls.get_adapter(name)
        return {
            "name": name,
            "class": adapter_class.__name__,
            "module": adapter_class.__module__,
            "supports_batch": hasattr(adapter_class, "supports_batch_operations"),
        }

    @classmethod
    def get_all_adapter_info(cls) -> list[dict[str, Any]]:
        """Get detailed information about all registered adapters.

        Returns:
            list[dict]: List of adapter information dictionaries

        Example:
            >>> all_info = StorageAdapterRegistry.get_all_adapter_info()
            >>> for info in all_info:
            >>>     print(f"{info['name']}: {info['class']}")
        """
        return [cls.get_adapter_info(name) for name in cls.list_available()]


def auto_discover_adapters() -> None:
    """Auto-discover and register all available storage adapters.

    Scans the adapters directory and automatically registers all adapter classes.
    Should be called during application startup.

    Example:
        ```python
        # In app startup (main.py)
        from src.app.infrastructure.storage.registry import auto_discover_adapters

        @app.on_event("startup")
        async def startup():
            auto_discover_adapters()
        ```
    """
    import importlib
    import pkgutil

    adapters_package = "src.app.infrastructure.storage.adapters"

    try:
        adapters_module = importlib.import_module(adapters_package)
    except ImportError:
        logger.warning(f"Could not import adapters package: {adapters_package}")
        return

    # Iterate over all modules in the adapters package
    for _, module_name, is_pkg in pkgutil.iter_modules(
        adapters_module.__path__, prefix=f"{adapters_package}."
    ):
        if is_pkg:
            continue  # Skip sub-packages

        try:
            module = importlib.import_module(module_name)

            # Find all StorageAdapter subclasses in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                # Check if it's a class and subclass of StorageAdapter
                if (
                    isinstance(attr, type)
                    and attr_name.endswith("Adapter")
                    and attr.__module__ == module_name
                ):
                    try:
                        from src.app.domain.interfaces.storage_adapter import (
                            StorageAdapter,
                        )

                        if issubclass(attr, StorageAdapter) and attr != StorageAdapter:
                            StorageAdapterRegistry.register(attr)
                            logger.info(f"Auto-discovered adapter: {attr.__name__}")
                    except TypeError:
                        # Not a StorageAdapter subclass
                        continue

        except Exception as e:
            logger.warning(f"Error loading adapter module {module_name}: {e}")

    registered_count = len(StorageAdapterRegistry.list_available())
    logger.info(
        f"Auto-discovery complete. Registered {registered_count} storage adapter(s): "
        f"{', '.join(StorageAdapterRegistry.list_available())}"
    )


__all__ = ["StorageAdapterRegistry", "auto_discover_adapters"]
