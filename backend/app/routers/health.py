"""
IdeaScope – Health check router.
Owner: Member 2 (Sufiyaan Imran)
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check")
def health_check(db: Session = Depends(get_db)):
    """SELECT 1 to verify database connectivity."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
