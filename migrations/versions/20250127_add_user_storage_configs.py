"""Add user_storage_configs and user_preferences tables

Revision ID: 20250127_storage_configs
Revises:
Create Date: 2025-01-27

Related ADR: ADR-014 (Storage Adapter Pattern), ADR-015 (User Preferences System)
Related RF: RF-019 (Multi-Storage Backend), RF-020 (User Preferences Management)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250127_storage_configs'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user_storage_configs and user_preferences tables."""

    # Create user_storage_configs table
    op.create_table(
        'user_storage_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, comment='NULL for single-user mode, UUID for multi-tenant'),
        sa.Column('adapter_name', sa.String(50), nullable=False, comment='Adapter type: notion, clickup, sheets'),
        sa.Column('config_json', postgresql.JSONB, nullable=False, comment='Adapter-specific configuration (api_key, database_id, etc)'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('true'), comment='Whether this config is active'),
        sa.Column('priority', sa.Integer, nullable=False, server_default=sa.text('0'), comment='Sync priority (higher = first)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), onupdate=sa.text('NOW()')),
        comment='Storage adapter configurations for multi-backend support'
    )

    # Create indexes for user_storage_configs
    op.create_index(
        'ix_user_storage_configs_user_id_active',
        'user_storage_configs',
        ['user_id', 'is_active'],
        comment='Fast lookup of active configs by user'
    )
    op.create_index(
        'ix_user_storage_configs_adapter_name',
        'user_storage_configs',
        ['adapter_name'],
        comment='Fast lookup by adapter type'
    )

    # Create user_preferences table
    op.create_table(
        'user_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, unique=True, comment='NULL for single-user mode'),
        sa.Column('brief_time', sa.Time, nullable=False, server_default=sa.text("'08:00:00'"), comment='Daily brief time (HH:MM:SS)'),
        sa.Column('timezone', sa.String(50), nullable=False, server_default=sa.text("'America/Sao_Paulo'"), comment='User timezone (IANA format)'),
        sa.Column('notification_channels', postgresql.JSONB, nullable=False, server_default=sa.text('\'["whatsapp"]\''), comment='Enabled notification channels'),
        sa.Column('deadline_reminder_hours', sa.Integer, nullable=False, server_default=sa.text('24'), comment='Hours before deadline to send reminder'),
        sa.Column('preferences_json', postgresql.JSONB, nullable=False, server_default=sa.text('\'{}\''), comment='Additional user preferences (flexible schema)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), onupdate=sa.text('NOW()')),
        comment='User preferences for ProactivityEngine and notifications'
    )

    # Create index for user_preferences
    op.create_index(
        'ix_user_preferences_user_id',
        'user_preferences',
        ['user_id'],
        unique=True,
        comment='Ensure one preference set per user'
    )

    # Add external_id column to tasks table if it doesn't exist
    # This is needed for storage adapter pattern
    try:
        op.add_column(
            'tasks',
            sa.Column('external_id', sa.String(255), nullable=True, comment='External ID from storage backend (Notion page ID, ClickUp task ID, etc)')
        )
        op.create_index(
            'ix_tasks_external_id',
            'tasks',
            ['external_id'],
            comment='Fast lookup by external ID'
        )
    except Exception:
        # Column might already exist
        pass


def downgrade() -> None:
    """Drop user_storage_configs and user_preferences tables."""

    # Drop indexes first
    op.drop_index('ix_user_preferences_user_id', table_name='user_preferences')
    op.drop_index('ix_user_storage_configs_adapter_name', table_name='user_storage_configs')
    op.drop_index('ix_user_storage_configs_user_id_active', table_name='user_storage_configs')

    # Drop tables
    op.drop_table('user_preferences')
    op.drop_table('user_storage_configs')

    # Drop external_id from tasks (optional, might lose data)
    try:
        op.drop_index('ix_tasks_external_id', table_name='tasks')
        op.drop_column('tasks', 'external_id')
    except Exception:
        # Column might not exist or might be needed by other code
        pass
