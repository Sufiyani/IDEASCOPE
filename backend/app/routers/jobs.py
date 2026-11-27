"""
IdeaScope – Jobs router.
Owner: Member 2 (Sufiyaan Imran)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.services import job_service

router = APIRouter(tags=["Jobs"])


@router.get("/{job_id}")
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    actor=Depends(get_current_user),
):
    return job_service.get_job(db, job_id, actor)
