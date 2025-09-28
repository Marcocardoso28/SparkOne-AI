"""Task management endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.db.repositories import update_task_status
from app.models.db.tasks import TaskRecord, TaskStatus

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskResponse(BaseModel):
    id: int
    title: str
    status: TaskStatus
    due_at: str | None
    channel: str
    sender: str

    @classmethod
    def from_orm(cls, record: TaskRecord) -> TaskResponse:
        return cls(
            id=record.id,
            title=record.title,
            status=record.status,
            due_at=record.due_at.isoformat() if record.due_at else None,
            channel=record.channel,
            sender=record.sender,
        )


class TaskUpdate(BaseModel):
    status: TaskStatus


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/", response_model=list[TaskResponse])
async def list_tasks(
    session: SessionDep,
    status_filter: TaskStatus | None = Query(None, alias="status"),
) -> list[TaskResponse]:
    stmt = select(TaskRecord).order_by(TaskRecord.id.desc())
    if status_filter is not None:
        stmt = stmt.where(TaskRecord.status == status_filter)
    result = await session.execute(stmt)
    records = result.scalars().all()
    return [TaskResponse.from_orm(record) for record in records]


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    session: SessionDep,
) -> TaskResponse:
    record = await update_task_status(session, task_id=task_id, status=payload.status)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await session.commit()
    await session.refresh(record)
    return TaskResponse.from_orm(record)


__all__ = ["router"]
