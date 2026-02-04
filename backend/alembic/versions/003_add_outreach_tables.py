"""Add outreach tables for Instantly.ai integration

Revision ID: 003_outreach
Revises: 002_leads
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_outreach"
down_revision: Union[str, None] = "002_leads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "instantly_connections",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("api_key", sa.Text(), nullable=False),
        sa.Column("workspace_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        "outreach_campaigns",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("instantly_campaign_id", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(500), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        "outreach_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id"), nullable=False, index=True),
        sa.Column("campaign_id", sa.String(255), nullable=False),
        sa.Column("campaign_name", sa.String(500), nullable=True),
        sa.Column("status", sa.String(50), default="pushed"),
        sa.Column("instantly_lead_id", sa.String(255), nullable=True),
        sa.Column("variables_sent", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("outreach_logs")
    op.drop_table("outreach_campaigns")
    op.drop_table("instantly_connections")
