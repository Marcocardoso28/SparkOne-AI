"""Dependency factories for FastAPI routes."""

from __future__ import annotations

from functools import lru_cache
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agents.agno import AgnoBridge
from app.agents.orchestrator import Orchestrator
from app.channels import GoogleSheetsAdapter, MessageNormalizer, WebUIAdapter, WhatsAppAdapter
from app.config import get_settings
from app.infrastructure.database.database import get_session_factory
from app.core.events import EventDispatcher, N8nWebhookSink
from app.infrastructure.integrations.caldav import CalDAVClient
from app.infrastructure.integrations.evolution_api import EvolutionAPIClient
from app.infrastructure.integrations.google_calendar import GoogleCalendarClient
from app.infrastructure.integrations.notion import NotionClient
from app.infrastructure.chat import ChatProviderRouter
from app.infrastructure.embeddings import EmbeddingProvider
from app.domain.services.brief import BriefService
from app.domain.services.calendar import CalendarService
from app.domain.services.classification import ClassificationService
from app.domain.services.embeddings import EmbeddingService
from app.domain.services.ingestion import IngestionService
from app.domain.services.memory import MemoryService
from app.domain.services.personal_coach import PersonalCoachService
from app.domain.services.tasks import TaskService
from app.domain.services.whatsapp import WhatsAppService


@lru_cache
def get_chat_provider() -> ChatProviderRouter:
    return ChatProviderRouter(settings=get_settings())


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    return EmbeddingProvider(settings=get_settings())


@lru_cache
def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    return get_session_factory()


async def get_ingestion_service():
    session_factory = _get_session_factory()
    session = session_factory()
    try:
        yield build_ingestion_service(session)
        # Commit apenas se houver mudanças pendentes
        if session.dirty or session.new or session.deleted:
            await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_brief_service():
    session_factory = _get_session_factory()
    session = session_factory()
    try:
        chat_provider = get_chat_provider()
        yield BriefService(session=session, chat_provider=chat_provider)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


__all__ = [
    "get_chat_provider",
    "get_embedding_provider",
    "get_message_normalizer",
    "get_ingestion_service",
    "build_ingestion_service",
    "get_evolution_client",
    "get_whatsapp_service",
    "get_notion_client",
    "get_google_calendar_client",
    "get_caldav_client",
    "get_brief_service",
]


@lru_cache
def _get_classification_service() -> ClassificationService:
    return ClassificationService(agno=_get_agno_bridge())


@lru_cache
def get_message_normalizer() -> MessageNormalizer:
    adapters = [WhatsAppAdapter(), GoogleSheetsAdapter(), WebUIAdapter()]
    return MessageNormalizer(adapters)


@lru_cache
def _get_event_dispatcher() -> EventDispatcher | None:
    settings = get_settings()
    if not settings.enable_event_dispatcher:
        return None

    sinks = []
    if settings.event_webhook_url:
        sinks.append(
            N8nWebhookSink(url=str(settings.event_webhook_url),
                           token=settings.event_webhook_token)
        )

    if not sinks:
        return None

    return EventDispatcher(sinks=sinks)


def get_embedding_provider_optional() -> EmbeddingProvider | None:
    settings = get_settings()
    if not settings.openai_api_key and not settings.local_llm_url:
        return None
    return get_embedding_provider()


@lru_cache
def _get_agno_bridge() -> AgnoBridge | None:
    chat_provider = get_chat_provider()
    if not chat_provider.available:
        return None
    return AgnoBridge(chat_provider=chat_provider)


def build_ingestion_service(session: AsyncSession) -> IngestionService:
    chat_provider = get_chat_provider()
    agno = _get_agno_bridge()
    classification = _get_classification_service()
    embedding_provider = get_embedding_provider_optional()
    embedding_service = EmbeddingService(
        session=session, provider=embedding_provider)
    settings = get_settings()
    notion_client = get_notion_client()
    try:
        default_timezone = ZoneInfo(settings.timezone)
    except Exception:  # pragma: no cover - fallback for invalid timezones
        default_timezone = ZoneInfo("UTC")
    task_service = TaskService(
        session=session,
        notion_client=notion_client,
        notion_database_id=settings.notion_database_id,
    )
    calendar_service = CalendarService(
        session=session,
        caldav_client=get_caldav_client(),
        google_client=get_google_calendar_client(),
        calendar_id=settings.calendar_primary_id,
        default_timezone=default_timezone,
    )
    coach_service = PersonalCoachService(chat_provider=chat_provider)
    memory_service = MemoryService(session=session)
    orchestrator = Orchestrator(
        classification=classification,
        task_service=task_service,
        calendar_service=calendar_service,
        coach_service=coach_service,
        agno_bridge=agno,
    )
    dispatcher = _get_event_dispatcher()
    return IngestionService(
        session=session,
        orchestrator=orchestrator,
        embedding_service=embedding_service,
        memory_service=memory_service,
        dispatcher=dispatcher,
    )


@lru_cache
def get_evolution_client() -> EvolutionAPIClient | None:
    settings = get_settings()
    if not settings.evolution_api_base_url or not settings.evolution_api_key:
        return None
    return EvolutionAPIClient(
        base_url=str(settings.evolution_api_base_url),
        token=settings.evolution_api_key,
        timeout=settings.evolution_api_timeout,
    )


@lru_cache
def get_whatsapp_service() -> WhatsAppService | None:
    client = get_evolution_client()
    if client is None:
        return None
    settings = get_settings()
    return WhatsAppService(client, max_retries=settings.whatsapp_send_max_retries)


@lru_cache
def get_notion_client() -> NotionClient | None:
    settings = get_settings()
    if not settings.notion_api_key:
        return None
    return NotionClient(token=settings.notion_api_key)


@lru_cache
def get_google_calendar_client() -> GoogleCalendarClient | None:
    settings = get_settings()
    if settings.calendar_provider != "google" or not settings.google_calendar_credentials_path:
        return None
    return GoogleCalendarClient(settings.google_calendar_credentials_path)


@lru_cache
def get_caldav_client() -> CalDAVClient | None:
    settings = get_settings()
    if settings.calendar_provider != "caldav" or not settings.caldav_url:
        return None
    if not settings.caldav_username or not settings.caldav_password:
        return None
    return CalDAVClient(
        url=str(settings.caldav_url),
        username=settings.caldav_username,
        password=settings.caldav_password,
    )
