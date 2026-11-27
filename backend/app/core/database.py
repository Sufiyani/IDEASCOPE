"""
IdeaScope – Database engine and session factory.
Owner: Member 2 (Sufiyaan Imran)
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Yield a SQLAlchemy Session; always closed on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
