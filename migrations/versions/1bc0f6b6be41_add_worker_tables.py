"""Create worker DLQ and job event tables

Revision ID: 1bc0f6b6be41
Revises: e5a8fecca705
Create Date: 2025-10-09 12:00:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1bc0f6b6be41"
down_revision = "e5a8fecca705"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "worker_dlq",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("job_name", sa.Text(), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_worker_dlq_job_name", "worker_dlq", ["job_name"])
    op.create_index("idx_worker_dlq_retry_count", "worker_dlq", ["retry_count"])

    op.create_table(
        "worker_job_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("job_name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("runtime_seconds", sa.Float(), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_worker_job_events_job_name", "worker_job_events", ["job_name"])
    op.create_index("idx_worker_job_events_created_at", "worker_job_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_worker_job_events_created_at", table_name="worker_job_events")
    op.drop_index("idx_worker_job_events_job_name", table_name="worker_job_events")
    op.drop_table("worker_job_events")

    op.drop_index("idx_worker_dlq_retry_count", table_name="worker_dlq")
    op.drop_index("idx_worker_dlq_job_name", table_name="worker_dlq")
    op.drop_table("worker_dlq")
