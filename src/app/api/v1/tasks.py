"""Task management endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.database import get_db_session
from app.infrastructure.database.models.repositories import update_task_status
from app.infrastructure.database.models.tasks import TaskRecord, TaskStatus

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: str | None
    due_date: str | None
    channel: str
    sender: str
    created_at: str
    updated_at: str

    @classmethod
    def from_orm(cls, record: TaskRecord) -> TaskResponse:
        return cls(
            id=record.id,
            title=record.title,
            description=record.description,
            status=record.status,
            priority=record.priority,
            due_date=record.due_date.isoformat() if record.due_date else None,
            channel=record.channel,
            sender=record.sender,
            created_at=record.created_at.isoformat(
            ) if record.created_at else "1970-01-01T00:00:00Z",
            updated_at=record.updated_at.isoformat(
            ) if record.updated_at else "1970-01-01T00:00:00Z",
        )


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    due_at: str | None = None
    channel: str
    sender: str
    priority: str | None = "medium"


class TaskUpdate(BaseModel):
    status: TaskStatus


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int
    limit: int
    offset: int


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    session: SessionDep,
) -> TaskResponse:
    # Parse due_at if provided
    due_at = None
    if payload.due_at:
        try:
            due_at = datetime.fromisoformat(
                payload.due_at.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid due_at format. Use ISO format (e.g., 2024-01-01T12:00:00Z)"
            )

    # Create new task record
    task_record = TaskRecord(
        title=payload.title,
        description=payload.description,
        due_date=due_at,
        channel=payload.channel,
        sender=payload.sender,
        priority=payload.priority,
        status="pending"
    )

    session.add(task_record)
    await session.commit()
    await session.refresh(task_record)

    return TaskResponse.from_orm(task_record)


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    session: SessionDep,
    status_filter: TaskStatus | None = Query(None, alias="status"),
    channel: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> TaskListResponse:
    # Build query
    stmt = select(TaskRecord).order_by(TaskRecord.id.desc())
    count_stmt = select(TaskRecord.id)

    if status_filter is not None:
        stmt = stmt.where(TaskRecord.status == status_filter)
        count_stmt = count_stmt.where(TaskRecord.status == status_filter)

    if channel is not None:
        stmt = stmt.where(TaskRecord.channel == channel)
        count_stmt = count_stmt.where(TaskRecord.channel == channel)

    # Get total count
    count_result = await session.execute(count_stmt)
    total = len(count_result.scalars().all())

    # Apply pagination
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    records = result.scalars().all()

    return TaskListResponse(
        tasks=[TaskResponse.from_orm(record) for record in records],
        total=total,
        limit=limit,
        offset=offset
    )


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    session: SessionDep,
) -> TaskResponse:
    record = await update_task_status(session, task_id=task_id, status=payload.status)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Preparar resposta antes do commit
    response_data = TaskResponse.from_orm(record)
    await session.commit()
    return response_data


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status_endpoint(
    task_id: int,
    payload: TaskUpdate,
    session: SessionDep,
) -> TaskResponse:
    """Update task status specifically."""
    # Buscar o registro primeiro
    record = await session.get(TaskRecord, task_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Atualizar o status
    record.status = payload.status

    # Preparar resposta ANTES do commit para evitar problemas com greenlet
    response_data = TaskResponse(
        id=record.id,
        title=record.title,
        description=record.description,
        status=record.status,
        priority=record.priority,
        due_date=record.due_date.isoformat() if record.due_date else None,
        channel=record.channel,
        sender=record.sender,
        created_at=record.created_at.isoformat(
        ) if record.created_at else "1970-01-01T00:00:00Z",
        updated_at=record.updated_at.isoformat(
        ) if record.updated_at else "1970-01-01T00:00:00Z",
    )

    await session.commit()
    return response_data


__all__ = ["router"]
