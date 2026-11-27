"""
IdeaScope – Declarative base for all SQLAlchemy models.
Owner: Member 2 (Sufiyaan Imran)
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base; all ORM models inherit from this."""
    pass
