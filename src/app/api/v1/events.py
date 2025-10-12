"""Calendar event endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.database import get_db_session
from app.infrastructure.database.models.events import EventRecord, EventStatus

router = APIRouter(prefix="/events", tags=["events"])


class EventResponse(BaseModel):
    id: int
    title: str
    status: EventStatus
    start_at: datetime
    end_at: datetime | None
    location: str | None

    @classmethod
    def from_record(cls, record: EventRecord) -> EventResponse:
        return cls(
            id=record.id,
            title=record.title,
            status=record.status,
            start_at=record.start_at,
            end_at=record.end_at,
            location=record.location,
        )


SessionDep = Depends(get_db_session)


@router.get("/", response_model=list[EventResponse])
async def list_events(
    session: AsyncSession = SessionDep,
    upcoming_only: bool = Query(True, description="Retorna apenas eventos a partir de agora"),
    limit: int = Query(20, le=100),
) -> list[EventResponse]:
    stmt = select(EventRecord).order_by(EventRecord.start_at.asc()).limit(limit)
    if upcoming_only:
        stmt = stmt.where(EventRecord.start_at >= datetime.now(UTC))
    result = await session.execute(stmt)
    return [EventResponse.from_record(row) for row in result.scalars()]


__all__ = ["router"]
