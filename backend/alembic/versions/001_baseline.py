"""Baseline migration - existing tables

Revision ID: 001_baseline
Revises:
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing tables are already created by Base.metadata.create_all()
    # This baseline migration just marks the starting point for Alembic.
    pass


def downgrade() -> None:
    pass
