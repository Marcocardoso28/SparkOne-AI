"""Worker service entrypoint providing scheduling and metrics."""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from time import perf_counter
from typing import Any, Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sqlalchemy import Select, and_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from zoneinfo import ZoneInfo

import structlog

from app.config import get_settings
from app.core.database import get_session_factory
from app.core.logging import configure_logging
from app.models.db.events import EventRecord, EventStatus
from app.models.db.tasks import TaskRecord, TaskStatus

from .event_monitor import EventMonitor
from .notification_manager import NotificationManager

JobHandler = Callable[[], Awaitable[dict[str, Any]]]

settings = get_settings()
configure_logging(debug=settings.debug)
logger = structlog.get_logger(__name__)

JOB_COUNT = Counter(
    "sparkone_worker_job_count_total",
    "Total executions for worker jobs",
    labelnames=["job_name", "status"],
)

JOB_LATENCY = Histogram(
    "sparkone_worker_job_latency_seconds",
    "Latency histogram for worker jobs",
    labelnames=["job_name"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10, 30),
)

TZ = ZoneInfo(settings.timezone)
JOB_DEFINITIONS = (
    {"id": "event-reminder", "interval_minutes": 5},
    {"id": "task-reminder", "interval_minutes": 5},
    {"id": "dlq-recovery", "interval_minutes": 2},
)

scheduler: AsyncIOScheduler | None = None
session_factory: async_sessionmaker[AsyncSession] | None = None
notification_manager: NotificationManager | None = None
event_monitor: EventMonitor | None = None


def _get_scheduler() -> AsyncIOScheduler | None:
    return scheduler or getattr(app, "scheduler", None)


def _get_session_factory() -> async_sessionmaker[AsyncSession] | None:
    return session_factory or getattr(app, "session_factory", None)


def _get_notification_manager() -> NotificationManager | None:
    return notification_manager or getattr(app, "notification_manager", None)


def _get_event_monitor() -> EventMonitor | None:
    return event_monitor or getattr(app, "event_monitor", None)


@dataclass(slots=True)
class JobResult:
    payload: dict[str, Any]
    alerts_dispatched: bool


async def _execute_job(job_name: str, handler: JobHandler) -> JobResult:
    _sched = _get_scheduler()
    _monitor = _get_event_monitor()
    _manager = _get_notification_manager()
    assert _sched is not None
    assert _monitor is not None
    assert _manager is not None

    started_at = datetime.now(tz=TZ)
    scheduled_for = started_at
    status = "success"
    error: str | None = None
    payload: dict[str, Any] | None = None
    alerts_dispatched = False
    elapsed_timer = perf_counter()

    try:
        payload = await handler()
        alerts_dispatched = bool(payload.get("alerts_dispatched")) if payload else False
        logger.info(
            "worker_job_succeeded",
            job_name=job_name,
            alerts_dispatched=alerts_dispatched,
            payload=payload,
        )
    except Exception as exc:  # pragma: no cover - runtime failure path
        status = "failure"
        error = str(exc)
        try:
            await _manager.enqueue_dlq(
                job_name=job_name,
                payload=payload,
                error=error,
                scheduled_for=scheduled_for,
            )
        except Exception as dlq_exc:  # pragma: no cover - defensive guard
            logger.error("worker_dlq_store_failed", job_name=job_name, error=str(dlq_exc))
        try:
            await _manager.send_alert(
                job_name=job_name,
                severity="critical",
                message=f"Job {job_name} failed: {error}",
                metadata={"phase": "worker"},
            )
        except Exception as alert_exc:  # pragma: no cover - defensive guard
            logger.error("worker_alert_dispatch_failed", job_name=job_name, error=str(alert_exc))
        raise
    finally:
        finished_at = datetime.now(tz=TZ)
        runtime_seconds = perf_counter() - elapsed_timer
        JOB_LATENCY.labels(job_name=job_name).observe(runtime_seconds)
        JOB_COUNT.labels(job_name=job_name, status=status).inc()
        try:
            await _monitor.record_job_event(
                job_name=job_name,
                status=status,
                runtime_seconds=runtime_seconds,
                started_at=started_at,
                finished_at=finished_at,
                scheduled_for=scheduled_for,
                payload=payload,
                error=error,
            )
        except Exception as monitor_exc:  # pragma: no cover - defensive guard
            logger.error("worker_event_monitor_failed", job_name=job_name, error=str(monitor_exc))

    return JobResult(payload=payload or {}, alerts_dispatched=alerts_dispatched)


async def _events_job() -> dict[str, Any]:
    _factory = _get_session_factory()
    _manager = _get_notification_manager()
    assert _factory is not None
    assert _manager is not None

    _EventRecord = getattr(app, "EventRecord", EventRecord)
    _EventStatus = getattr(app, "EventStatus", EventStatus)

    async with _factory() as session:
        now = datetime.now(tz=TZ)
        window_end = now + timedelta(minutes=60)
        query: Select[tuple[_EventRecord]] = select(_EventRecord).where(
            and_(
                _EventRecord.status != _EventStatus.CANCELLED,
                _EventRecord.start_at >= now,
                _EventRecord.start_at <= window_end,
            )
        ).order_by(_EventRecord.start_at)
        result = await session.execute(query)
        upcoming = result.scalars().all()

    deliveries = {"sent": 0, "queued": 0, "deliveries": []}
    if upcoming:
        preview = [
            {
                "id": event.id,
                "title": event.title,
                "starts_at": event.start_at.isoformat(),
            }
            for event in upcoming[:5]
        ]
        deliveries = await _manager.send_alert(
            job_name="event-reminder",
            severity="info",
            message=f"{len(upcoming)} eventos nas próximas 60 minutos",
            metadata={"preview": preview},
        )

    return {
        "alerts_dispatched": bool(upcoming),
        "upcoming_events": len(upcoming),
        "window_minutes": 60,
        "deliveries": deliveries,
    }


async def _tasks_job() -> dict[str, Any]:
    _factory = _get_session_factory()
    _manager = _get_notification_manager()
    assert _factory is not None
    assert _manager is not None

    _TaskRecord = getattr(app, "TaskRecord", TaskRecord)
    _TaskStatus = getattr(app, "TaskStatus", TaskStatus)

    async with _factory() as session:
        now = datetime.now(tz=TZ)
        window_end = now + timedelta(minutes=90)
        query: Select[tuple[_TaskRecord]] = select(_TaskRecord).where(
            and_(
                _TaskRecord.status != _TaskStatus.DONE,
                _TaskRecord.due_at.isnot(None),
                _TaskRecord.due_at >= now,
                _TaskRecord.due_at <= window_end,
            )
        ).order_by(_TaskRecord.due_at)
        result = await session.execute(query)
        due_tasks = result.scalars().all()

    deliveries = {"sent": 0, "queued": 0, "deliveries": []}
    if due_tasks:
        preview = [
            {
                "id": task.id,
                "title": task.title,
                "due_at": task.due_at.isoformat() if task.due_at else None,
            }
            for task in due_tasks[:5]
        ]
        deliveries = await _manager.send_alert(
            job_name="task-reminder",
            severity="warning",
            message=f"{len(due_tasks)} tarefas vencem em até 90 minutos",
            metadata={"preview": preview},
        )

    return {
        "alerts_dispatched": bool(due_tasks),
        "due_tasks": len(due_tasks),
        "window_minutes": 90,
        "deliveries": deliveries,
    }


async def run_event_reminder() -> JobResult:
    return await _execute_job("event-reminder", _events_job)


async def run_task_reminder() -> JobResult:
    return await _execute_job("task-reminder", _tasks_job)


async def _dlq_job() -> dict[str, Any]:
    _manager = _get_notification_manager()
    assert _manager is not None

    result = await _manager.reprocess_dlq(limit=25)
    return {
        "alerts_dispatched": bool(result["success"]),
        "attempted": result["attempted"],
        "success": result["success"],
        "failure": result["failure"],
    }


async def run_dlq_recovery() -> JobResult:
    return await _execute_job("dlq-recovery", _dlq_job)


def _prime_metrics() -> None:
    for definition in JOB_DEFINITIONS:
        job_id = definition["id"]
        JOB_COUNT.labels(job_name=job_id, status="success")
        JOB_COUNT.labels(job_name=job_id, status="failure")
        JOB_LATENCY.labels(job_name=job_id)


def _schedule_jobs(current_scheduler: AsyncIOScheduler) -> None:
    now = datetime.now(tz=TZ)
    for definition in JOB_DEFINITIONS:
        handler = {
            "event-reminder": run_event_reminder,
            "task-reminder": run_task_reminder,
            "dlq-recovery": run_dlq_recovery,
        }[definition["id"]]
        current_scheduler.add_job(
            handler,
            trigger=IntervalTrigger(minutes=definition["interval_minutes"], timezone=TZ),
            id=definition["id"],
            replace_existing=True,
            coalesce=True,
            misfire_grace_time=120,
            max_instances=1,
            next_run_time=now,
        )


@asynccontextmanager
async def _lifespan(_: FastAPI):
    global scheduler, session_factory, notification_manager, event_monitor

    session_factory = get_session_factory()
    notification_manager = NotificationManager(session_factory=session_factory)
    event_monitor = EventMonitor(session_factory=session_factory)
    scheduler = AsyncIOScheduler(timezone=TZ)
    _prime_metrics()
    _schedule_jobs(scheduler)
    scheduler.start()
    logger.info("worker_scheduler_started")

    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)
        logger.info("worker_scheduler_stopped")


app = FastAPI(title="SparkOne Worker", version="0.1.0", lifespan=_lifespan)


@app.get("/healthz")
async def healthz() -> JSONResponse:
    if scheduler is None:
        return JSONResponse({"status": "error", "message": "scheduler not initialised"}, status_code=503)
    stats = {
        "jobs": scheduler.get_jobs(),
        "timezone": str(TZ),
    }
    return JSONResponse(
        {
            "status": "ok",
            "jobs": [job.id for job in stats["jobs"]],
            "timezone": stats["timezone"],
        }
    )


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


__all__ = ["app", "run_event_reminder", "run_task_reminder", "run_dlq_recovery"]

# Expose internals on the FastAPI app object for tests that import
# `services.worker.app as worker_app` and expect module-level attributes.
setattr(app, "scheduler", scheduler)
setattr(app, "session_factory", session_factory)
setattr(app, "notification_manager", notification_manager)
setattr(app, "event_monitor", event_monitor)
setattr(app, "EventRecord", EventRecord)
setattr(app, "EventStatus", EventStatus)
setattr(app, "TaskRecord", TaskRecord)
setattr(app, "TaskStatus", TaskStatus)
setattr(app, "TZ", TZ)
setattr(app, "run_event_reminder", run_event_reminder)
setattr(app, "run_task_reminder", run_task_reminder)
setattr(app, "run_dlq_recovery", run_dlq_recovery)
