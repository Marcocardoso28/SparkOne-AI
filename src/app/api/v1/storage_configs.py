"""API endpoints for storage adapter configuration management.

Provides CRUD operations for user_storage_configs, allowing users to:
- List active storage configurations
- Create new storage adapter configurations
- Update existing configurations
- Delete configurations
- List available adapters from registry

Related to: ADR-014 (Storage Adapter Pattern), RF-019, RF-020
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.database import get_db_session
from app.infrastructure.database.models.user_storage_config import UserStorageConfig
from app.infrastructure.storage.registry import StorageAdapterRegistry

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/storage-configs", tags=["Storage Configuration"])


# Pydantic schemas
class StorageConfigCreate(BaseModel):
    """Schema for creating a new storage configuration."""

    adapter_name: str = Field(
        ...,
        description="Adapter type: notion, clickup, sheets",
        examples=["notion", "clickup", "sheets"],
    )
    config_json: dict[str, Any] = Field(
        ...,
        description="Adapter-specific configuration (api_key, database_id, etc)",
        examples=[
            {
                "api_key": "secret_xxx",
                "database_id": "abc123",
            }
        ],
    )
    is_active: bool = Field(
        True,
        description="Whether this config should be active",
    )
    priority: int = Field(
        0,
        description="Sync priority (higher = first)",
        ge=0,
        le=100,
    )


class StorageConfigUpdate(BaseModel):
    """Schema for updating an existing storage configuration."""

    config_json: dict[str, Any] | None = Field(
        None,
        description="Updated adapter configuration",
    )
    is_active: bool | None = Field(
        None,
        description="Update active status",
    )
    priority: int | None = Field(
        None,
        description="Update priority",
        ge=0,
        le=100,
    )


class StorageConfigResponse(BaseModel):
    """Schema for storage configuration response."""

    id: UUID
    user_id: UUID | None
    adapter_name: str
    config_json: dict[str, Any]
    is_active: bool
    priority: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class AvailableAdapter(BaseModel):
    """Schema for available adapter information."""

    name: str
    description: str
    required_fields: list[str]


@router.get(
    "",
    response_model=list[StorageConfigResponse],
    summary="List storage configurations",
    description="Retrieve all storage configurations for the current user (single-user mode: user_id=None)",
)
async def list_storage_configs(
    session: AsyncSession = Depends(get_db_session),
    user_id: UUID | None = None,
) -> list[StorageConfigResponse]:
    """List all storage configurations for user.

    Args:
        session: Database session
        user_id: User ID (None for single-user mode)

    Returns:
        List of storage configurations
    """
    stmt = (
        select(UserStorageConfig)
        .where(UserStorageConfig.user_id == user_id)
        .order_by(UserStorageConfig.priority.desc(), UserStorageConfig.created_at.desc())
    )

    result = await session.execute(stmt)
    configs = result.scalars().all()

    return [
        StorageConfigResponse(
            id=config.id,
            user_id=config.user_id,
            adapter_name=config.adapter_name,
            config_json=config.config_json,
            is_active=config.is_active,
            priority=config.priority,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat(),
        )
        for config in configs
    ]


@router.post(
    "",
    response_model=StorageConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create storage configuration",
    description="Create a new storage adapter configuration",
)
async def create_storage_config(
    config: StorageConfigCreate,
    session: AsyncSession = Depends(get_db_session),
    user_id: UUID | None = None,
) -> StorageConfigResponse:
    """Create a new storage configuration.

    Args:
        config: Configuration data
        session: Database session
        user_id: User ID (None for single-user mode)

    Returns:
        Created configuration

    Raises:
        HTTPException: If adapter not found or validation fails
    """
    # Validate adapter exists
    try:
        StorageAdapterRegistry.get_adapter(config.adapter_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown adapter: {config.adapter_name}",
        )

    # Create new config
    new_config = UserStorageConfig(
        user_id=user_id,
        adapter_name=config.adapter_name,
        config_json=config.config_json,
        is_active=config.is_active,
        priority=config.priority,
    )

    session.add(new_config)
    await session.commit()
    await session.refresh(new_config)

    logger.info(
        "storage_config_created",
        adapter=config.adapter_name,
        user_id=str(user_id) if user_id else "single_user",
        priority=config.priority,
    )

    return StorageConfigResponse(
        id=new_config.id,
        user_id=new_config.user_id,
        adapter_name=new_config.adapter_name,
        config_json=new_config.config_json,
        is_active=new_config.is_active,
        priority=new_config.priority,
        created_at=new_config.created_at.isoformat(),
        updated_at=new_config.updated_at.isoformat(),
    )


@router.put(
    "/{config_id}",
    response_model=StorageConfigResponse,
    summary="Update storage configuration",
    description="Update an existing storage configuration",
)
async def update_storage_config(
    config_id: UUID,
    updates: StorageConfigUpdate,
    session: AsyncSession = Depends(get_db_session),
    user_id: UUID | None = None,
) -> StorageConfigResponse:
    """Update an existing storage configuration.

    Args:
        config_id: Configuration ID to update
        updates: Update data
        session: Database session
        user_id: User ID (None for single-user mode)

    Returns:
        Updated configuration

    Raises:
        HTTPException: If configuration not found
    """
    # Fetch existing config
    stmt = select(UserStorageConfig).where(
        UserStorageConfig.id == config_id,
        UserStorageConfig.user_id == user_id,
    )
    result = await session.execute(stmt)
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Storage config {config_id} not found",
        )

    # Apply updates
    if updates.config_json is not None:
        config.config_json = updates.config_json
    if updates.is_active is not None:
        config.is_active = updates.is_active
    if updates.priority is not None:
        config.priority = updates.priority

    await session.commit()
    await session.refresh(config)

    logger.info(
        "storage_config_updated",
        config_id=str(config_id),
        adapter=config.adapter_name,
        user_id=str(user_id) if user_id else "single_user",
    )

    return StorageConfigResponse(
        id=config.id,
        user_id=config.user_id,
        adapter_name=config.adapter_name,
        config_json=config.config_json,
        is_active=config.is_active,
        priority=config.priority,
        created_at=config.created_at.isoformat(),
        updated_at=config.updated_at.isoformat(),
    )


@router.delete(
    "/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete storage configuration",
    description="Delete a storage configuration",
)
async def delete_storage_config(
    config_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    user_id: UUID | None = None,
) -> None:
    """Delete a storage configuration.

    Args:
        config_id: Configuration ID to delete
        session: Database session
        user_id: User ID (None for single-user mode)

    Raises:
        HTTPException: If configuration not found
    """
    # Fetch config
    stmt = select(UserStorageConfig).where(
        UserStorageConfig.id == config_id,
        UserStorageConfig.user_id == user_id,
    )
    result = await session.execute(stmt)
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Storage config {config_id} not found",
        )

    await session.delete(config)
    await session.commit()

    logger.info(
        "storage_config_deleted",
        config_id=str(config_id),
        adapter=config.adapter_name,
        user_id=str(user_id) if user_id else "single_user",
    )


@router.get(
    "/available",
    response_model=list[AvailableAdapter],
    summary="List available adapters",
    description="Get list of all available storage adapters from registry",
)
async def list_available_adapters() -> list[AvailableAdapter]:
    """List all available storage adapters.

    Returns:
        List of available adapters with metadata
    """
    available = StorageAdapterRegistry.list_available()

    adapters = []
    for name in available:
        info = StorageAdapterRegistry.get_adapter_info(name)
        adapters.append(
            AvailableAdapter(
                name=name,
                description=info.get("description", f"{name.title()} storage adapter"),
                required_fields=info.get("required_fields", []),
            )
        )

    return adapters


__all__ = ["router"]
