"""
IdeaScope – Job service (read-only for the API; writes via worker/queue.py).
Owner: Member 2 (Sufiyaan Imran)
"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.constants import ROLE_STUDENT
from app.models.job import Job
from app.models.user import User
from app.services.auth_service import _user_to_dict  # noqa – shared helper


def _job_to_dict(job: Job) -> dict:
    def _fmt(dt):
        return dt.isoformat() if dt else None

    return {
        "id": job.id,
        "type": job.type,
        "target_id": job.target_id,
        "status": job.status,
        "progress": job.progress,
        "attempts": job.attempts,
        "error": job.error,
        "result": job.result,
        "created_by": job.created_by,
        "created_at": _fmt(job.created_at),
        "started_at": _fmt(job.started_at),
        "finished_at": _fmt(job.finished_at),
    }


def get_job(db: Session, job_id: int, actor: User) -> dict:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_not_found")

    is_admin = actor.role != ROLE_STUDENT
    is_creator = job.created_by == actor.id

    if not (is_admin or is_creator):
        raise HTTPException(status_code=403, detail="forbidden")

    return _job_to_dict(job)
