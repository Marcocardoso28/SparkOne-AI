"""create channel messages table

Revision ID: 0001
Revises: 
Create Date: 2025-01-01 00:00:00
"""

from __future__ import annotations

import sys
from pathlib import Path

import sqlalchemy as sa
from alembic import op

# Ensure project root is on path so 'src' package resolves
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.app.models.schemas import Channel, MessageType

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Skip vector extension for SQLite
    # op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "channel_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("channel", sa.Enum(Channel, name="channel_enum"), nullable=False),
        sa.Column("sender", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("message_type", sa.Enum(MessageType, name="message_type_enum"), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "message_embeddings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "message_id",
            sa.Integer(),
            sa.ForeignKey("channel_messages.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("embedding", sa.Text(), nullable=False),  # Using Text for SQLite compatibility
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "document_id",
            sa.Integer(),
            sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=False),  # Using Text for SQLite compatibility
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "sheets_sync_state",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("spreadsheet_id", sa.String(), nullable=False),
        sa.Column("range_name", sa.String(), nullable=False),
        sa.Column("last_row_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("sender", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("user", "assistant", name="conversation_role_enum"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("todo", "in_progress", "done", name="task_status_enum"),
            nullable=False,
            server_default="todo",
        ),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("sender", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("confirmed", "tentative", "cancelled", name="event_status_enum"),
            nullable=False,
            server_default="confirmed",
        ),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("sender", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_table("events")
    op.drop_table("tasks")
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_documents")
    op.drop_table("sheets_sync_state")
    op.drop_table("conversation_messages")
    op.drop_table("message_embeddings")
    op.drop_table("channel_messages")
    sa.Enum(name="channel_enum").drop(bind, checkfirst=False)
    sa.Enum(name="message_type_enum").drop(bind, checkfirst=False)
    sa.Enum(name="task_status_enum").drop(bind, checkfirst=False)
    sa.Enum(name="event_status_enum").drop(bind, checkfirst=False)
    sa.Enum(name="conversation_role_enum").drop(bind, checkfirst=False)
