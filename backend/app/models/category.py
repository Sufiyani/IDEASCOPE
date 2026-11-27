"""
IdeaScope – Category model.
Owner: Member 2 (Sufiyaan Imran)

Table: categories (2 columns)
id is SMALLINT 1..12, NOT auto-generated.
"""

from __future__ import annotations

from sqlalchemy import SmallInteger, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Category(Base):
    __tablename__ = "categories"

    __table_args__ = (UniqueConstraint("name", name="uq_categories_name"),)

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
