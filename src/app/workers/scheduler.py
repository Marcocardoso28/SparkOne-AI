"""ProactivityEngine Scheduler - ADR-016.

Manages background jobs for automated reminders and proactive notifications:
- Daily brief (configurable time via user_preferences)
- Deadline reminders (24h before due date)
- Overdue checks (every 6 hours)
- Event reminders (30 min before event)
- Google Sheets sync (every 5 min)

Related to: ADR-016 (ProactivityEngine Architecture), RF-015
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from zoneinfo import ZoneInfo

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.infrastructure.database.database import get_session_factory
from app.core.metrics import (
    FALLBACK_NOTIFICATION_COUNTER,
    SHEETS_SYNC_COUNTER,
    WHATSAPP_NOTIFICATION_COUNTER,
)
from app.api.dependencies import (
    build_ingestion_service,
    get_message_normalizer,
    get_whatsapp_service,
)
from app.infrastructure.integrations.google_sheets import GoogleSheetsClient
from app.infrastructure.chat import ChatProviderRouter
from app.domain.services.brief import BriefService
from app.domain.services.email import send_email
from app.domain.services.google_sheets_sync import GoogleSheetsSyncService

# Import new ProactivityEngine jobs
from app.workers.jobs import (
    send_daily_brief,
    check_deadlines,
    check_overdue,
    event_reminders,
)

logger = structlog.get_logger(__name__)


@lru_cache
def _get_chat_provider() -> ChatProviderRouter:
    return ChatProviderRouter(settings=get_settings())


async def daily_brief_job() -> None:
    """Generate the daily brief placeholder using the persona."""

    chat_provider = _get_chat_provider()
    session_factory = get_session_factory()
    async with session_factory() as session:
        brief_service = BriefService(
            session=session, chat_provider=chat_provider)
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
        logger.debug("whatsapp_notification_skipped",
                     reason="service not configured")
        return

    numbers = [num.strip() for num in numbers_raw.split(",") if num.strip()]
    for number in numbers:
        try:
            await whatsapp_service.send_text(number, message)
            WHATSAPP_NOTIFICATION_COUNTER.labels(status="success").inc()
        except Exception as exc:  # pragma: no cover - external failure path
            WHATSAPP_NOTIFICATION_COUNTER.labels(status="failure").inc()
            logger.warning("whatsapp_notification_failed",
                           number=number, error=str(exc))
            await _fallback_notification(message)


async def _fallback_notification(message: str) -> None:
    settings = get_settings()
    email = settings.fallback_email
    if not email:
        return
    FALLBACK_NOTIFICATION_COUNTER.labels(status="sent").inc()
    await send_email("SparkOne Alerta", message)
    logger.info("fallback_notification", email=email,
                message_preview=message[:120])


async def main() -> None:
    """Run APScheduler with proactive jobs.

    Configures and starts all ProactivityEngine jobs:
    1. Daily brief - 08:00 (configurable via user_preferences)
    2. Deadline reminders - Every hour
    3. Overdue checks - Every 6 hours
    4. Event reminders - Every 5 minutes
    5. Sheets sync - Every 5 minutes (legacy)

    Graceful shutdown on SIGTERM/SIGINT.
    """

    settings = get_settings()
    timezone = ZoneInfo(settings.timezone)
    scheduler = AsyncIOScheduler(timezone=timezone)

    # Legacy jobs (keep for backward compatibility)
    scheduler.add_job(
        daily_brief_job,
        trigger=CronTrigger(hour=7, minute=30, timezone=timezone),
        id="daily-brief-legacy",
        replace_existing=True,
        misfire_grace_time=300,
        jitter=60,
        max_instances=1,
    )

    scheduler.add_job(
        sheets_sync_job,
        trigger=IntervalTrigger(minutes=5, timezone=timezone),
        id="sheets-sync",
        replace_existing=True,
        misfire_grace_time=120,
        jitter=15,
        max_instances=1,
    )

    # ProactivityEngine jobs (new)
    scheduler.add_job(
        send_daily_brief,
        trigger=CronTrigger(hour=8, minute=0, timezone=timezone),
        id="proactivity-daily-brief",
        replace_existing=True,
        misfire_grace_time=300,
        jitter=60,
        max_instances=1,
        kwargs={"user_id": None},  # Single-user mode
    )

    scheduler.add_job(
        check_deadlines,
        trigger=IntervalTrigger(hours=1, timezone=timezone),
        id="proactivity-deadline-reminders",
        replace_existing=True,
        misfire_grace_time=300,
        max_instances=1,
        kwargs={"user_id": None},
    )

    scheduler.add_job(
        check_overdue,
        trigger=IntervalTrigger(hours=6, timezone=timezone),
        id="proactivity-overdue-check",
        replace_existing=True,
        misfire_grace_time=600,
        max_instances=1,
        kwargs={"user_id": None},
    )

    scheduler.add_job(
        event_reminders,
        trigger=IntervalTrigger(minutes=5, timezone=timezone),
        id="proactivity-event-reminders",
        replace_existing=True,
        misfire_grace_time=120,
        max_instances=1,
        kwargs={"user_id": None},
    )

    scheduler.start()
    logger.info(
        "scheduler_started",
        timezone=settings.timezone,
        jobs=len(scheduler.get_jobs()),
    )

    try:
        # Keep scheduler running
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, asyncio.CancelledError):  # pragma: no cover - runtime guard
        logger.info("scheduler_stopping", reason="shutdown_signal")
    finally:
        scheduler.shutdown(wait=True)
        logger.info("scheduler_stopped")


if __name__ == "__main__":  # pragma: no cover - manual execution guard
    asyncio.run(main())
