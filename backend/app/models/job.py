"""
IdeaScope – Job model (background job queue).
Owner: Member 2 (Sufiyaan Imran)

Table: jobs (12 columns)
Job types: 'import_file' | 'process_abstract' | 'analyze_proposal' | 'generate_proposal'
Status:    'queued' | 'running' | 'done' | 'failed'
No payload column – target_id references the entity the job works on.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Job(Base):
    __tablename__ = "jobs"

    __table_args__ = (
        CheckConstraint(
            "type IN ('import_file','process_abstract','analyze_proposal','generate_proposal')",
            name="ck_jobs_type",
        ),
        CheckConstraint(
            "status IN ('queued','running','done','failed')",
            name="ck_jobs_status",
        ),
        CheckConstraint("progress >= 0 AND progress <= 100", name="ck_jobs_progress"),
        Index("ix_jobs_status_created_at", "status", "created_at"),
        Index("ix_jobs_created_by", "created_by"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="queued")
    progress: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
