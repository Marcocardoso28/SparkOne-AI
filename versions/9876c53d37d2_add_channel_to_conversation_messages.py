"""add_channel_to_conversation_messages

Revision ID: 9876c53d37d2
Revises: 0002
Create Date: 2025-09-23 21:32:36.005077

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '9876c53d37d2'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add channel column to conversation_messages table
    op.add_column('conversation_messages', sa.Column('channel', sa.String(length=50), nullable=False, server_default='web'))
    
    # Add sender column to conversation_messages table
    op.add_column('conversation_messages', sa.Column('sender', sa.String(length=100), nullable=False, server_default='unknown'))


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('conversation_messages', 'sender')
    op.drop_column('conversation_messages', 'channel')