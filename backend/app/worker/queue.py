"""
IdeaScope – Job enqueue helper.
Owner: Member 2 (Sufiyaan Imran)

Members 1 and 3 import enqueue_job() to create background jobs.
"""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.constants import VALID_JOB_TYPES
from app.models.job import Job


def enqueue_job(
    db: Session,
    job_type: str,
    target_id: int,
    created_by: Optional[int] = None,
) -> Job:
    """
    Create a new Job with status 'queued' and flush it to the session.

    Args:
        db:         SQLAlchemy session (caller owns commit).
        job_type:   One of the VALID_JOB_TYPES constants.
        target_id:  PK of the entity the job operates on.
        created_by: User ID of the requesting user (optional).

    Returns:
        The new Job ORM object (not yet committed).

    Raises:
        HTTPException 400 if job_type is not valid.
    """
    if job_type not in VALID_JOB_TYPES:
        raise HTTPException(status_code=400, detail="invalid_job_type")

    job = Job(
        type=job_type,
        target_id=target_id,
        status="queued",
        created_by=created_by,
    )
    db.add(job)
    db.flush()
    return job
