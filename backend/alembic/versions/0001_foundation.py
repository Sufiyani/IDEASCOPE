"""Foundation: vector extension, categories, sdgs

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable pgvector extension (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── categories ────────────────────────────────────────────────────────────
    op.create_table(
        "categories",
        sa.Column("id", sa.SmallInteger(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.UniqueConstraint("name", name="uq_categories_name"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── sdgs ──────────────────────────────────────────────────────────────────
    op.create_table(
        "sdgs",
        sa.Column("number", sa.SmallInteger(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.UniqueConstraint("name", name="uq_sdgs_name"),
        sa.PrimaryKeyConstraint("number"),
    )


def downgrade() -> None:
    op.drop_table("sdgs")
    op.drop_table("categories")
    # Leave the vector extension in place (other migrations may use it)
