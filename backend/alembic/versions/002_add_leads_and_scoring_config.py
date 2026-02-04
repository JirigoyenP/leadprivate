"""Add leads and scoring_configs tables

Revision ID: 002_leads
Revises: 001_baseline
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_leads"
down_revision: Union[str, None] = "001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("last_name", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(500), nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("phone", sa.String(100), nullable=True),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("company_name", sa.String(500), nullable=True),
        sa.Column("company_domain", sa.String(255), nullable=True),
        sa.Column("company_industry", sa.String(255), nullable=True),
        sa.Column("company_size", sa.Integer(), nullable=True),
        sa.Column("company_location", sa.String(500), nullable=True),
        sa.Column("verification_status", sa.String(50), nullable=True),
        sa.Column("verification_sub_status", sa.String(100), nullable=True),
        sa.Column("verification_score", sa.Integer(), nullable=True),
        sa.Column("enriched", sa.Boolean(), default=False),
        sa.Column("seniority", sa.String(100), nullable=True),
        sa.Column("headline", sa.Text(), nullable=True),
        sa.Column("city", sa.String(255), nullable=True),
        sa.Column("state", sa.String(255), nullable=True),
        sa.Column("country", sa.String(255), nullable=True),
        sa.Column("departments", sa.JSON(), nullable=True),
        sa.Column("phone_numbers", sa.JSON(), nullable=True),
        sa.Column("lead_score", sa.Integer(), default=0),
        sa.Column("score_breakdown", sa.JSON(), nullable=True),
        sa.Column("source", sa.String(50), default="csv"),
        sa.Column("outreach_status", sa.String(50), nullable=True),
        sa.Column("latest_verification_id", sa.Integer(), sa.ForeignKey("email_verifications.id"), nullable=True),
        sa.Column("latest_enrichment_id", sa.Integer(), sa.ForeignKey("contact_enrichments.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_leads_score", "leads", ["lead_score"])
    op.create_index("ix_leads_source", "leads", ["source"])
    op.create_index("ix_leads_verification_status", "leads", ["verification_status"])
    op.create_index("ix_leads_outreach_status", "leads", ["outreach_status"])
    op.create_index("ix_leads_created_at", "leads", ["created_at"])

    op.create_table(
        "scoring_configs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False, default="default"),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("scoring_configs")
    op.drop_index("ix_leads_created_at", table_name="leads")
    op.drop_index("ix_leads_outreach_status", table_name="leads")
    op.drop_index("ix_leads_verification_status", table_name="leads")
    op.drop_index("ix_leads_source", table_name="leads")
    op.drop_index("ix_leads_score", table_name="leads")
    op.drop_table("leads")
