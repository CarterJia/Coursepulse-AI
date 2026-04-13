"""Change embedding vector dimension from 1536 to 512 for local sentence-transformers

Revision ID: 0002
Revises: 0001
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE embeddings DROP COLUMN IF EXISTS vector")
    op.execute("ALTER TABLE embeddings ADD COLUMN vector vector(512)")


def downgrade() -> None:
    op.execute("ALTER TABLE embeddings DROP COLUMN IF EXISTS vector")
    op.execute("ALTER TABLE embeddings ADD COLUMN vector vector(1536)")
