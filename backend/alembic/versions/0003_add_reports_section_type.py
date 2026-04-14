"""Add section_type column to reports

Revision ID: 0003
Revises: 0002
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "reports",
        sa.Column(
            "section_type",
            sa.String(length=32),
            nullable=False,
            server_default="topic",
        ),
    )


def downgrade() -> None:
    op.drop_column("reports", "section_type")
