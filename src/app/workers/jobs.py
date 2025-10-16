"""ProactivityEngine background jobs for automated reminders and briefs.

Contains job implementations for:
- Daily brief (08:00 AM default, configurable via user_preferences)
- Deadline reminders (24h before due date)
- Overdue task checks (every 6 hours)
- Event reminders (30 min before event)

Related to: ADR-016 (ProactivityEngine Architecture), RF-015
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.metrics import WHATSAPP_NOTIFICATION_COUNTER
from app.domain.services.brief import BriefService
from app.infrastructure.chat import ChatProviderRouter
from app.infrastructure.database.database import get_session_factory
from app.infrastructure.database.models.tasks import TaskRecord, TaskStatus
from app.infrastructure.database.models.user_preferences import UserPreferences

logger = structlog.get_logger(__name__)


async def send_daily_brief(user_id: str | None = None) -> None:
    """Generate and send daily brief to user via WhatsApp.

    Fetches tasks and events for the day, generates a personalized brief
    using the user's persona, and sends via WhatsApp.

    Args:
        user_id: User ID to send brief to (None for single-user mode)

    Related to: RF-015 (ProactivityEngine)
    """
    from app.api.dependencies import get_whatsapp_service

    settings = get_settings()
    session_factory = get_session_factory()

    async with session_factory() as session:
        try:
            # Load user preferences
            prefs = await _load_user_preferences(session, user_id)
            if not prefs:
                logger.debug("daily_brief_skipped", reason="no_user_preferences")
                return

            # Check if WhatsApp is enabled for this user
            if "whatsapp" not in prefs.notification_channels:
                logger.debug(
                    "daily_brief_skipped",
                    reason="whatsapp_not_enabled",
                    user_id=user_id,
                )
                return

            # Generate brief
            chat_provider = ChatProviderRouter(settings=settings)
            brief_service = BriefService(session=session, chat_provider=chat_provider)
            content = await brief_service.textual_brief()

            # Send via WhatsApp
            whatsapp_service = get_whatsapp_service()
            if whatsapp_service and prefs.whatsapp_number:
                await whatsapp_service.send_text(prefs.whatsapp_number, content)
                WHATSAPP_NOTIFICATION_COUNTER.labels(status="success").inc()
                logger.info(
                    "daily_brief_sent",
                    user_id=user_id,
                    chars=len(content),
                )
            else:
                logger.warning(
                    "daily_brief_skipped",
                    reason="whatsapp_not_configured",
                    user_id=user_id,
                )

            await session.commit()

        except Exception as exc:  # pragma: no cover - job failure path
            await session.rollback()
            logger.warning("daily_brief_failed", error=str(exc), user_id=user_id)
            WHATSAPP_NOTIFICATION_COUNTER.labels(status="failure").inc()


async def check_deadlines(user_id: str | None = None) -> None:
    """Check for tasks with deadlines approaching in 24 hours and send reminders.

    Queries tasks with due dates within the configured reminder window
    (default: 24 hours) and sends WhatsApp notifications.

    Args:
        user_id: User ID to check tasks for (None for single-user mode)

    Related to: RF-015 (ProactivityEngine)
    """
    from app.api.dependencies import get_whatsapp_service

    session_factory = get_session_factory()

    async with session_factory() as session:
        try:
            # Load user preferences
            prefs = await _load_user_preferences(session, user_id)
            if not prefs or "whatsapp" not in prefs.notification_channels:
                logger.debug(
                    "deadline_reminder_skipped",
                    reason="whatsapp_not_enabled",
                    user_id=user_id,
                )
                return

            # Calculate reminder window
            now = datetime.utcnow()
            reminder_window = now + timedelta(hours=prefs.deadline_reminder_hours)

            # Query tasks with approaching deadlines
            stmt = (
                select(TaskRecord)
                .where(
                    TaskRecord.due_at.is_not(None),
                    TaskRecord.due_at <= reminder_window,
                    TaskRecord.due_at > now,
                    TaskRecord.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
                    TaskRecord.reminded_at.is_(None),  # Not already reminded
                )
                .order_by(TaskRecord.due_at.asc())
            )

            result = await session.execute(stmt)
            tasks = result.scalars().all()

            if not tasks:
                logger.debug(
                    "deadline_reminder_skipped",
                    reason="no_upcoming_deadlines",
                    user_id=user_id,
                )
                return

            # Build reminder message
            task_list = "\n".join(
                [
                    f"" {task.title} - Prazo: {task.due_at.strftime('%d/%m/%Y %H:%M')}"
                    for task in tasks
                ]
            )
            message = f"ð Lembretes de Prazo:\n\n{task_list}\n\nNão esqueça!"

            # Send reminder
            whatsapp_service = get_whatsapp_service()
            if whatsapp_service and prefs.whatsapp_number:
                await whatsapp_service.send_text(prefs.whatsapp_number, message)
                WHATSAPP_NOTIFICATION_COUNTER.labels(status="success").inc()

                # Mark tasks as reminded
                for task in tasks:
                    task.reminded_at = now
                    session.add(task)

                logger.info(
                    "deadline_reminders_sent",
                    user_id=user_id,
                    count=len(tasks),
                )

            await session.commit()

        except Exception as exc:  # pragma: no cover - job failure path
            await session.rollback()
            logger.warning("deadline_reminder_failed", error=str(exc), user_id=user_id)
            WHATSAPP_NOTIFICATION_COUNTER.labels(status="failure").inc()


async def check_overdue(user_id: str | None = None) -> None:
    """Check for overdue tasks and send notifications.

    Identifies tasks past their due date and still not completed,
    sending WhatsApp notifications to the user.

    Args:
        user_id: User ID to check tasks for (None for single-user mode)

    Related to: RF-015 (ProactivityEngine)
    """
    from app.api.dependencies import get_whatsapp_service

    session_factory = get_session_factory()

    async with session_factory() as session:
        try:
            # Load user preferences
            prefs = await _load_user_preferences(session, user_id)
            if not prefs or "whatsapp" not in prefs.notification_channels:
                logger.debug(
                    "overdue_check_skipped",
                    reason="whatsapp_not_enabled",
                    user_id=user_id,
                )
                return

            # Query overdue tasks
            now = datetime.utcnow()
            stmt = (
                select(TaskRecord)
                .where(
                    TaskRecord.due_at.is_not(None),
                    TaskRecord.due_at < now,
                    TaskRecord.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
                )
                .order_by(TaskRecord.due_at.asc())
            )

            result = await session.execute(stmt)
            tasks = result.scalars().all()

            if not tasks:
                logger.debug(
                    "overdue_check_skipped",
                    reason="no_overdue_tasks",
                    user_id=user_id,
                )
                return

            # Build overdue message
            task_list = "\n".join(
                [
                    f"" {task.title} - Atrasada desde: {task.due_at.strftime('%d/%m/%Y')}"
                    for task in tasks
                ]
            )
            message = f"  Tarefas Atrasadas ({len(tasks)}):\n\n{task_list}\n\nPor favor, atualize o status!"

            # Send notification
            whatsapp_service = get_whatsapp_service()
            if whatsapp_service and prefs.whatsapp_number:
                await whatsapp_service.send_text(prefs.whatsapp_number, message)
                WHATSAPP_NOTIFICATION_COUNTER.labels(status="success").inc()

                logger.info(
                    "overdue_notification_sent",
                    user_id=user_id,
                    count=len(tasks),
                )

            await session.commit()

        except Exception as exc:  # pragma: no cover - job failure path
            await session.rollback()
            logger.warning("overdue_check_failed", error=str(exc), user_id=user_id)
            WHATSAPP_NOTIFICATION_COUNTER.labels(status="failure").inc()


async def event_reminders(user_id: str | None = None) -> None:
    """Send reminders for events starting in 30 minutes.

    Checks for events (tasks with specific start times) and sends
    WhatsApp notifications 30 minutes before they begin.

    Args:
        user_id: User ID to check events for (None for single-user mode)

    Related to: RF-015 (ProactivityEngine)

    Note:
        Current implementation treats tasks with due_at as potential events.
        Future enhancement: separate events table with start_at/end_at fields.
    """
    from app.api.dependencies import get_whatsapp_service

    session_factory = get_session_factory()

    async with session_factory() as session:
        try:
            # Load user preferences
            prefs = await _load_user_preferences(session, user_id)
            if not prefs or "whatsapp" not in prefs.notification_channels:
                logger.debug(
                    "event_reminder_skipped",
                    reason="whatsapp_not_enabled",
                    user_id=user_id,
                )
                return

            # Calculate event window (30 minutes ahead)
            now = datetime.utcnow()
            event_window_start = now + timedelta(minutes=25)  # 5min buffer
            event_window_end = now + timedelta(minutes=35)

            # Query tasks/events in the window
            stmt = (
                select(TaskRecord)
                .where(
                    TaskRecord.due_at.is_not(None),
                    TaskRecord.due_at >= event_window_start,
                    TaskRecord.due_at <= event_window_end,
                    TaskRecord.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
                    TaskRecord.reminded_at.is_(None),  # Not already reminded
                )
                .order_by(TaskRecord.due_at.asc())
            )

            result = await session.execute(stmt)
            events = result.scalars().all()

            if not events:
                logger.debug(
                    "event_reminder_skipped",
                    reason="no_upcoming_events",
                    user_id=user_id,
                )
                return

            # Build event reminder message
            event_list = "\n".join(
                [
                    f"" {event.title} - Às {event.due_at.strftime('%H:%M')}"
                    for event in events
                ]
            )
            message = f"= Eventos em 30 minutos:\n\n{event_list}\n\nPrepare-se!"

            # Send reminder
            whatsapp_service = get_whatsapp_service()
            if whatsapp_service and prefs.whatsapp_number:
                await whatsapp_service.send_text(prefs.whatsapp_number, message)
                WHATSAPP_NOTIFICATION_COUNTER.labels(status="success").inc()

                # Mark events as reminded
                for event in events:
                    event.reminded_at = now
                    session.add(event)

                logger.info(
                    "event_reminders_sent",
                    user_id=user_id,
                    count=len(events),
                )

            await session.commit()

        except Exception as exc:  # pragma: no cover - job failure path
            await session.rollback()
            logger.warning("event_reminder_failed", error=str(exc), user_id=user_id)
            WHATSAPP_NOTIFICATION_COUNTER.labels(status="failure").inc()


async def _load_user_preferences(
    session: AsyncSession,
    user_id: str | None,
) -> UserPreferences | None:
    """Load user preferences from database.

    Args:
        session: Database session
        user_id: User ID (None for single-user mode)

    Returns:
        UserPreferences or None if not found
    """
    stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


__all__ = [
    "send_daily_brief",
    "check_deadlines",
    "check_overdue",
    "event_reminders",
]
