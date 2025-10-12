"""convert embeddings column to pgvector and add ivfflat index

Revision ID: 2f0b0e7d1a10
Revises: 1bc0f6b6be41
Create Date: 2025-10-12 13:35:00
"""

from __future__ import annotations

from alembic import op


revision = "2f0b0e7d1a10"
down_revision = "1bc0f6b6be41"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":  # no-op for non-Postgres
        return

    # Ensure pgvector extension is available
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Convert column type to vector(1536) if possible (table is expected to be empty on fresh prod)
    op.execute(
        """
        DO $$
        BEGIN
            BEGIN
                ALTER TABLE message_embeddings
                ALTER COLUMN embedding TYPE vector(1536)
                USING embedding::vector(1536);
            EXCEPTION WHEN others THEN
                -- Leave as-is if conversion fails (operator will re-run later)
                RAISE NOTICE 'Skipping vector conversion for message_embeddings.embedding';
            END;
        END$$;
        """
    )

    # Create IVFFlat index if column is vector
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='message_embeddings'
                  AND column_name='embedding'
                  AND udt_name='vector'
            ) THEN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = 'ix_message_embeddings_embedding_ivfflat'
                ) THEN
                    CREATE INDEX ix_message_embeddings_embedding_ivfflat
                        ON message_embeddings USING ivfflat (embedding vector_l2_ops)
                        WITH (lists = 100);
                END IF;
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("DROP INDEX IF EXISTS ix_message_embeddings_embedding_ivfflat;")
    # keep column as vector; reversing to previous text/json type is optional and lossy

