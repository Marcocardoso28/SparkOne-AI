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

from ..config import get_settings
from ..core.database import get_db_session
from ..dependencies import get_chat_provider, get_notion_client, get_evolution_client

from ..models.schemas import HealthStatus

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=HealthStatus)
async def healthcheck() -> HealthStatus:
    """Return basic service status."""

    return HealthStatus(status="ok")


@router.get("/database", response_model=HealthStatus)
async def database_health(session: AsyncSession = Depends(get_db_session)) -> HealthStatus:
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:  # pragma: no cover - db failure path
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="database unavailable") from exc
    return HealthStatus(status="ok")


@router.get("/redis", response_model=HealthStatus)
async def redis_health() -> HealthStatus:
    settings = get_settings()
    if not settings.redis_url or Redis is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="redis not configured")

    client = Redis.from_url(settings.redis_url)
    try:
        pong = await client.ping()
    except Exception as exc:  # pragma: no cover - redis failure path
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="redis unavailable") from exc
    finally:
        await client.close()
    if not pong:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="redis unavailable")
    return HealthStatus(status="ok")


@router.get("/openai", response_model=HealthStatus)
async def openai_health() -> HealthStatus:
    provider = get_chat_provider()
    if not provider.available:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="openai provider unavailable")
    return HealthStatus(status="ok")


@router.get("/notion", response_model=HealthStatus)
async def notion_health() -> HealthStatus:
    client = get_notion_client()
    if client is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="notion not configured")
    return HealthStatus(status="ok")


@router.get("/evolution", response_model=HealthStatus)
async def evolution_health() -> HealthStatus:
    client = get_evolution_client()
    if client is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="evolution not configured")
    return HealthStatus(status="ok")
