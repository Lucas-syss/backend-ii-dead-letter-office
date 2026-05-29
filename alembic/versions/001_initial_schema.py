"""Initial schema: events and incidents tables.

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── events ────────────────────────────────────────────────
    op.create_table(
        "events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("service", sa.String(100), nullable=False),
        sa.Column("error_code", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_source", "events", ["source"])
    op.create_index("ix_events_status", "events", ["status"])
    op.create_index("ix_events_service", "events", ["service"])

    # ── incidents ─────────────────────────────────────────────
    op.create_table(
        "incidents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("remediation_attempted", sa.Boolean(), nullable=False),
        sa.Column("remediation_result", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(4), nullable=False),
        sa.Column("report_md", sa.Text(), nullable=False),
        sa.Column("escalated", sa.Boolean(), nullable=False),
        sa.Column("raw_agent_output", sa.JSON(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index("ix_incidents_severity", "incidents", ["severity"])
    op.create_index("ix_incidents_event_type", "incidents", ["event_type"])


def downgrade() -> None:
    op.drop_table("incidents")
    op.drop_table("events")