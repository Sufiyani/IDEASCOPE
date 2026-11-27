"""
IdeaScope – Group and GroupMember models.
Owner: Member 2 (Sufiyaan Imran)

Tables: groups (5 columns), group_members (3 columns, composite PK)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Group(Base):
    __tablename__ = "groups"

    __table_args__ = (Index("ix_groups_leader_id", "leader_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    batch: Mapped[str] = mapped_column(Text, nullable=False)
    leader_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class GroupMember(Base):
    __tablename__ = "group_members"

    __table_args__ = (
        PrimaryKeyConstraint("group_id", "user_id", name="pk_group_members"),
        # A student is in only one group
        UniqueConstraint("user_id", name="uq_group_members_user_id"),
        Index("ix_group_members_group_id", "group_id"),
    )

    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
