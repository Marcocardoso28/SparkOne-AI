"""rename metadata to extra_data

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-21 12:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename metadata column to extra_data in channel_messages table
    op.alter_column(
        "channel_messages",
        "metadata",
        new_column_name="extra_data"
    )
    
    # Rename metadata column to extra_data in knowledge_documents table
    op.alter_column(
        "knowledge_documents", 
        "metadata",
        new_column_name="extra_data"
    )


def downgrade() -> None:
    # Rename extra_data column back to metadata in knowledge_documents table
    op.alter_column(
        "knowledge_documents",
        "extra_data", 
        new_column_name="metadata"
    )
    
    # Rename extra_data column back to metadata in channel_messages table
    op.alter_column(
        "channel_messages",
        "extra_data",
        new_column_name="metadata"
    )