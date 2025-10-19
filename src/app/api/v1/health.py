"""Healthcheck endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from redis.asyncio import Redis
except ImportError:  # pragma: no cover - optional dependency absent
    Redis = None  # type: ignore

from app.config import get_settings
from app.infrastructure.database.database import get_db_session
from app.api.dependencies import get_chat_provider, get_evolution_client, get_notion_client
from app.models.schemas import HealthStatus, DatabaseHealthStatus, RedisHealthStatus

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=HealthStatus)
async def healthcheck() -> HealthStatus:
    """Return basic service status."""

    return HealthStatus(status="ok")


# Handle both '/health/' and '/health' explicitly to avoid redirect issues in healthchecks
@router.get("", response_model=HealthStatus)
async def healthcheck_no_slash() -> HealthStatus:
    return HealthStatus(status="ok")


@router.get("/database", response_model=DatabaseHealthStatus)
async def database_health(session: AsyncSession = Depends(get_db_session)) -> DatabaseHealthStatus:
    try:
        await session.execute(text("SELECT 1"))
        return DatabaseHealthStatus(status="ok", database="sqlite", connected=True)
    except SQLAlchemyError as exc:  # pragma: no cover - db failure path
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="database unavailable"
        ) from exc


@router.get("/redis", response_model=RedisHealthStatus)
async def redis_health() -> RedisHealthStatus:
    settings = get_settings()
    if not settings.redis_url or Redis is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="redis not configured"
        )

    client = Redis.from_url(settings.redis_url)
    try:
        pong = await client.ping()
        return RedisHealthStatus(status="ok", redis="redis", connected=pong)
    except Exception as exc:  # pragma: no cover - redis failure path
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="redis unavailable"
        ) from exc
    finally:
        await client.close()


@router.get("/openai", response_model=HealthStatus)
async def openai_health() -> HealthStatus:
    provider = get_chat_provider()
    if not provider.available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="openai provider unavailable"
        )
    return HealthStatus(status="ok")


@router.get("/notion", response_model=HealthStatus)
async def notion_health() -> HealthStatus:
    client = get_notion_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="notion not configured"
        )
    return HealthStatus(status="ok")


@router.get("/evolution", response_model=HealthStatus)
async def evolution_health() -> HealthStatus:
    client = get_evolution_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="evolution not configured"
        )
    return HealthStatus(status="ok")
