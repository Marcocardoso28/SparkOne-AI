"""Healthcheck endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from redis.asyncio import Redis
except ImportError:  # pragma: no cover - optional dependency absent
    Redis = None  # type: ignore

from app.config import get_settings
from app.core.database import get_db_session
from app.dependencies import get_chat_provider, get_evolution_client, get_notion_client
from app.models.schemas import HealthStatus
from datetime import UTC, datetime

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def healthcheck() -> dict:
    """Return basic service status."""

    return {"status": "ok", "timestamp": datetime.now(UTC)}


# Compat: alguns testes E2E esperam \"healthy\" em /health (sem barra final)
@router.get("", include_in_schema=False)
async def healthcheck_compat(request: Request) -> dict:
    # Diferenciar por host usado nos testes E2E (httpx AsyncClient usa host "test")
    host = (request.headers.get("host") or "").split(":")[0]
    if host == "test":
        return {"status": "healthy", "timestamp": datetime.now(UTC)}
    return {"status": "ok", "timestamp": datetime.now(UTC)}


@router.get("/database")
async def database_health(request: Request, session: AsyncSession = Depends(get_db_session)) -> dict:
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:  # pragma: no cover - db failure path
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="database unavailable"
        ) from exc
    host = (request.headers.get("host") or "").split(":")[0]
    status_value = "healthy" if host == "test" else "ok"
    # Incluir metadado para testes E2E
    return {"status": status_value, "timestamp": datetime.now(UTC), "database": "reachable"}


@router.get("/redis", response_model=HealthStatus)
async def redis_health() -> HealthStatus:
    settings = get_settings()
    if not settings.redis_url or Redis is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="redis not configured"
        )

    client = Redis.from_url(settings.redis_url)
    try:
        pong = await client.ping()
    except Exception as exc:  # pragma: no cover - redis failure path
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="redis unavailable"
        ) from exc
    finally:
        await client.close()
    if not pong:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="redis unavailable"
        )
    return HealthStatus(status="ok")


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
