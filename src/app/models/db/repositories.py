"""Repository helpers for persistence operations."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.profiler import profile_query, profile_session
from app.models.schemas import ChannelMessage

from .events import EventRecord, EventStatus
from .knowledge import KnowledgeChunkORM, KnowledgeDocumentORM
from .memory import ConversationMessage, ConversationRole
from .message import ChannelMessageORM
from .sheets import SheetsSyncStateORM
from .tasks import TaskRecord, TaskStatus
from .vector import MessageEmbeddingORM


@profile_query
async def save_channel_message(session: AsyncSession, payload: ChannelMessage) -> ChannelMessageORM:
    """
    Persiste mensagem normalizada no banco de dados.
    Função crítica para performance - monitora tempo de inserção.
    """
    async with profile_session(session, "save_channel_message"):
        instance = ChannelMessageORM(
            channel=payload.channel,
            sender=payload.sender,
            content=payload.content,
            message_type=payload.message_type,
            occurred_at=payload.created_at,
            extra_data=payload.extra_data,
        )
        session.add(instance)
        await session.flush()
        return instance


@profile_query
async def list_recent_messages(
    session: AsyncSession, limit: int = 50
) -> Sequence[ChannelMessageORM]:
    """
    Retorna mensagens mais recentes ingeridas.
    Query crítica para dashboard - monitora performance de SELECT com LIMIT.
    """
    async with profile_session(session, "list_recent_messages"):
        result = await session.execute(
            select(ChannelMessageORM).order_by(ChannelMessageORM.id.desc()).limit(limit)
        )
        return tuple(result.scalars())


@profile_query
async def upsert_message_embedding(
    session: AsyncSession,
    *,
    message_id: int,
    embedding: list[float],
    content: str,
) -> MessageEmbeddingORM:
    """
    Persiste embeddings de mensagens, substituindo valor anterior se necessário.
    Operação crítica para busca semântica - monitora performance de UPSERT.
    """
    async with profile_session(session, "upsert_message_embedding"):
        result = await session.execute(
            select(MessageEmbeddingORM).where(MessageEmbeddingORM.message_id == message_id)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.embedding = embedding
            existing.content = content
            session.add(existing)
            return existing

        instance = MessageEmbeddingORM(message_id=message_id, embedding=embedding, content=content)
        session.add(instance)
        await session.flush()
        return instance


__all__ = [
    "save_channel_message",
    "list_recent_messages",
    "upsert_message_embedding",
    "create_knowledge_document",
    "insert_knowledge_chunks",
    "get_sheets_sync_state",
    "update_sheets_sync_state",
    "create_task",
    "update_task_status",
    "create_event",
    "append_conversation_message",
    "list_recent_conversations",
]


async def create_knowledge_document(
    session: AsyncSession,
    *,
    title: str,
    source: str,
    metadata: dict | None = None,
) -> KnowledgeDocumentORM:
    instance = KnowledgeDocumentORM(title=title, source=source, extra_data=metadata or {})
    session.add(instance)
    await session.flush()
    return instance


async def insert_knowledge_chunks(
    session: AsyncSession,
    *,
    document_id: int,
    chunks: Sequence[tuple[int, str, list[float]]],
) -> Sequence[KnowledgeChunkORM]:
    stored: list[KnowledgeChunkORM] = []
    for index, content, embedding in chunks:
        chunk = KnowledgeChunkORM(
            document_id=document_id,
            chunk_index=index,
            content=content,
            embedding=embedding,
        )
        session.add(chunk)
        stored.append(chunk)
    await session.flush()
    return tuple(stored)


async def get_sheets_sync_state(
    session: AsyncSession,
    *,
    spreadsheet_id: str,
    range_name: str,
) -> SheetsSyncStateORM | None:
    stmt = select(SheetsSyncStateORM).where(
        SheetsSyncStateORM.spreadsheet_id == spreadsheet_id,
        SheetsSyncStateORM.range_name == range_name,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_sheets_sync_state(
    session: AsyncSession,
    *,
    spreadsheet_id: str,
    range_name: str,
    last_row_index: int,
) -> SheetsSyncStateORM:
    state = await get_sheets_sync_state(
        session,
        spreadsheet_id=spreadsheet_id,
        range_name=range_name,
    )
    if state is None:
        state = SheetsSyncStateORM(
            spreadsheet_id=spreadsheet_id,
            range_name=range_name,
            last_row_index=last_row_index,
        )
    else:
        state.last_row_index = last_row_index
    session.add(state)
    await session.flush()
    return state


async def create_task(
    session: AsyncSession,
    *,
    title: str,
    description: str | None,
    due_at: datetime | None,
    channel: str,
    sender: str,
    status: TaskStatus = TaskStatus.TODO,
    external_id: str | None = None,
) -> TaskRecord:
    record = TaskRecord(
        title=title,
        description=description,
        due_at=due_at,
        channel=channel,
        sender=sender,
        status=status,
        external_id=external_id,
    )
    session.add(record)
    await session.flush()
    return record


async def update_task_status(
    session: AsyncSession,
    *,
    task_id: int,
    status: TaskStatus,
) -> TaskRecord | None:
    record = await session.get(TaskRecord, task_id)
    if record is None:
        return None
    record.status = status
    session.add(record)
    await session.flush()
    return record


async def create_event(
    session: AsyncSession,
    *,
    title: str,
    description: str | None,
    start_at: datetime,
    end_at: datetime | None,
    location: str | None,
    status: EventStatus = EventStatus.CONFIRMED,
    channel: str,
    sender: str,
    external_id: str | None = None,
) -> EventRecord:
    record = EventRecord(
        title=title,
        description=description,
        start_at=start_at,
        end_at=end_at,
        location=location,
        status=status,
        channel=channel,
        sender=sender,
        external_id=external_id,
    )
    session.add(record)
    await session.flush()
    return record


async def append_conversation_message(
    session: AsyncSession,
    *,
    conversation_id: str,
    channel: str,
    sender: str,
    role: ConversationRole,
    content: str,
) -> ConversationMessage:
    record = ConversationMessage(
        conversation_id=conversation_id,
        channel=channel,
        sender=sender,
        role=role,
        content=content,
    )
    session.add(record)
    await session.flush()
    return record


async def list_recent_conversations(
    session: AsyncSession,
    *,
    limit: int = 20,
) -> Sequence[ConversationMessage]:
    result = await session.execute(
        select(ConversationMessage).order_by(ConversationMessage.id.desc()).limit(limit)
    )
    return tuple(result.scalars())
