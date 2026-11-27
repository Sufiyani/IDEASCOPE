"""Jobs table

Revision ID: 0003
Revises: 0002
Create Date: 2025-01-01 00:02:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'queued'")),
        sa.Column("progress", sa.SmallInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("attempts", sa.SmallInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("result", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "type IN ('import_file','process_abstract','analyze_proposal','generate_proposal')",
            name="ck_jobs_type",
        ),
        sa.CheckConstraint(
            "status IN ('queued','running','done','failed')",
            name="ck_jobs_status",
        ),
        sa.CheckConstraint("progress >= 0 AND progress <= 100", name="ck_jobs_progress"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_status_created_at", "jobs", ["status", "created_at"])
    op.create_index("ix_jobs_created_by", "jobs", ["created_by"])


def downgrade() -> None:
    op.drop_index("ix_jobs_created_by", table_name="jobs")
    op.drop_index("ix_jobs_status_created_at", table_name="jobs")
    op.drop_table("jobs")
