"""Add is_admin column to users

Revision ID: 0004_add_is_admin
Revises: 0003_create_users_table
Create Date: 2025-10-12
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0004_add_is_admin"
down_revision = "0003_create_users_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()))

    # remove server_default after backfilling existing rows
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("is_admin", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("is_admin")

