"""Scheduler worker responsible for proactive routines."""

from __future__ import annotations

import asyncio
from functools import lru_cache
from zoneinfo import ZoneInfo

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.core.database import get_session_factory
from app.core.metrics import (
    FALLBACK_NOTIFICATION_COUNTER,
    SHEETS_SYNC_COUNTER,
    WHATSAPP_NOTIFICATION_COUNTER,
)
from app.dependencies import build_ingestion_service, get_message_normalizer, get_whatsapp_service
from app.integrations.google_sheets import GoogleSheetsClient
from app.providers.chat import ChatProviderRouter
from app.services.brief import BriefService
from app.services.email import send_email
from app.services.google_sheets_sync import GoogleSheetsSyncService

logger = structlog.get_logger(__name__)


@lru_cache
def _get_chat_provider() -> ChatProviderRouter:
    return ChatProviderRouter(settings=get_settings())


async def daily_brief_job() -> None:
    """Generate the daily brief placeholder using the persona."""

    chat_provider = _get_chat_provider()
    session_factory = get_session_factory()
    async with session_factory() as session:
        brief_service = BriefService(session=session, chat_provider=chat_provider)
        try:
            content = await brief_service.textual_brief()
            await session.commit()
            logger.info("daily_brief_generated")
            await _notify_whatsapp(content)
        except Exception as exc:  # pragma: no cover - job failure path
            await session.rollback()
            logger.warning("daily_brief_failed", error=str(exc))


async def sheets_sync_job() -> None:
    """Synchronize Google Sheets rows into the system."""

    settings = get_settings()
    credentials_path = settings.google_sheets_credentials_path
    spreadsheet_id = settings.google_sheets_sync_spreadsheet_id
    range_name = settings.google_sheets_sync_range
    if not credentials_path or not spreadsheet_id or not range_name:
        logger.debug(
            "sheets_sync_skipped",
            reason="Missing credentials or spreadsheet info",
        )
        return

    try:
        client = GoogleSheetsClient(credentials_path)
    except Exception as exc:  # pragma: no cover - environment setup issue
        logger.warning("sheets_client_init_failed", error=str(exc))
        return

    session_factory = get_session_factory()
    async with session_factory() as session:
        ingestion = build_ingestion_service(session)
        normalizer = get_message_normalizer()
        service = GoogleSheetsSyncService(
            session=session,
            client=client,
            normalizer=normalizer,
            ingestion_service=ingestion,
            spreadsheet_id=spreadsheet_id,
            range_name=range_name,
        )
        try:
            result = await service.sync()
            await session.commit()
            logger.info("sheets_sync_completed", **result)
        except Exception as exc:  # pragma: no cover - runtime failure path
            await session.rollback()
            SHEETS_SYNC_COUNTER.labels(status="failure").inc()
            logger.warning("sheets_sync_failed", error=str(exc))


async def _notify_whatsapp(message: str) -> None:
    settings = get_settings()
    numbers_raw = settings.whatsapp_notify_numbers
    if not numbers_raw:
        return

    whatsapp_service = get_whatsapp_service()
    if whatsapp_service is None:
        logger.debug("whatsapp_notification_skipped", reason="service not configured")
        return

    numbers = [num.strip() for num in numbers_raw.split(",") if num.strip()]
    for number in numbers:
        try:
            await whatsapp_service.send_text(number, message)
            WHATSAPP_NOTIFICATION_COUNTER.labels(status="success").inc()
        except Exception as exc:  # pragma: no cover - external failure path
            WHATSAPP_NOTIFICATION_COUNTER.labels(status="failure").inc()
            logger.warning("whatsapp_notification_failed", number=number, error=str(exc))
            await _fallback_notification(message)


async def _fallback_notification(message: str) -> None:
    settings = get_settings()
    email = settings.fallback_email
    if not email:
        return
    FALLBACK_NOTIFICATION_COUNTER.labels(status="sent").inc()
    await send_email("SparkOne Alerta", message)
    logger.info("fallback_notification", email=email, message_preview=message[:120])


async def main() -> None:
    """Run APScheduler with cron jobs for proactive routines."""

    settings = get_settings()
    scheduler = AsyncIOScheduler(timezone=ZoneInfo(settings.timezone))
    scheduler.add_job(
        daily_brief_job,
        trigger=CronTrigger(hour=7, minute=30, timezone=ZoneInfo(settings.timezone)),
        id="daily-brief",
        replace_existing=True,
        misfire_grace_time=300,
        jitter=60,
        max_instances=1,
    )

    scheduler.add_job(
        sheets_sync_job,
        trigger=IntervalTrigger(minutes=5, timezone=ZoneInfo(settings.timezone)),
        id="sheets-sync",
        replace_existing=True,
        misfire_grace_time=120,
        jitter=15,
        max_instances=1,
    )

    scheduler.start()
    logger.info("scheduler_started")

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, asyncio.CancelledError):  # pragma: no cover - runtime guard
        logger.info("scheduler_stopping")
    finally:
        scheduler.shutdown()


if __name__ == "__main__":  # pragma: no cover - manual execution guard
    asyncio.run(main())
