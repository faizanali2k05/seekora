"""Add privacy-minimal search analytics."""

import sqlalchemy as sa

from alembic import op

revision = "0002_search_analytics"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "search_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("query", sa.String(length=300), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_search_events_created_at", "search_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("search_events")
