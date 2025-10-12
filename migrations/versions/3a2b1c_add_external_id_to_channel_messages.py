"""add external_id to channel_messages

Revision ID: 3a2b1c
Revises: 2f0b0e7d1a10
Create Date: 2025-10-12 20:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "3a2b1c"
down_revision = "2f0b0e7d1a10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("channel_messages") as batch_op:
        batch_op.add_column(sa.Column("external_id", sa.String(length=255), nullable=True))
        batch_op.create_index(
            "ix_channel_messages_external_id", "external_id", unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("channel_messages") as batch_op:
        batch_op.drop_index("ix_channel_messages_external_id")
        batch_op.drop_column("external_id")

