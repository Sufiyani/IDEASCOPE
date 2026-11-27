"""
IdeaScope – SDG model (17 UN Sustainable Development Goals).
Owner: Member 2 (Sufiyaan Imran)

Table: sdgs (2 columns)
number is SMALLINT 1..17, NOT auto-generated.
"""

from __future__ import annotations

from sqlalchemy import SmallInteger, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SDG(Base):
    __tablename__ = "sdgs"

    __table_args__ = (UniqueConstraint("name", name="uq_sdgs_name"),)

    number: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
