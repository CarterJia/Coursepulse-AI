"""Add video_recommendations table

Revision ID: 0004
Revises: 0003_add_reports_section_type
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003_add_reports_section_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "video_recommendations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("document_id", sa.Uuid(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("topic_title", sa.String(512), nullable=False),
        sa.Column("bilibili_url", sa.String(512), nullable=False),
        sa.Column("bvid", sa.String(64), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("cover_url", sa.String(512), nullable=False),
        sa.Column("up_name", sa.String(256), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("play_count", sa.Integer(), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("video_recommendations")
