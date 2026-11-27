"""
IdeaScope – Background job runner.
Owner: Member 2 (Sufiyaan Imran)

Run as: python -m app.worker.runner
"""

from __future__ import annotations

import logging
import signal
import time
import traceback
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import (
    JOB_STATUS_DONE,
    JOB_STATUS_FAILED,
    JOB_STATUS_RUNNING,
    MAX_JOB_ATTEMPTS,
)
from app.core.database import SessionLocal
from app.models.job import Job
from app.worker.registry import get_handler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("ideascope.worker")

POLL_INTERVAL = 2  # seconds
_running = True


def _now() -> datetime:
    return datetime.now(UTC)


def _handle_sigterm(signum, frame):
    global _running
    logger.info("SIGTERM received – shutting down after current job")
    _running = False


signal.signal(signal.SIGTERM, _handle_sigterm)


def _claim_and_run(db: Session) -> bool:
    """Claim one queued job and run it. Returns True if a job was processed."""
    # SELECT ... FOR UPDATE SKIP LOCKED – only one worker claims each job
    job = db.scalar(
        select(Job)
        .where(Job.status == "queued")
        .order_by(Job.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if job is None:
        return False

    job.status = JOB_STATUS_RUNNING
    job.started_at = _now()
    job.attempts = (job.attempts or 0) + 1
    job.progress = 0
    db.commit()

    logger.info("Running job %d type=%s attempt=%d", job.id, job.type, job.attempts)

    handler = get_handler(job.type)
    if handler is None:
        job.status = JOB_STATUS_FAILED
        job.error = "no_handler_registered"
        job.finished_at = _now()
        db.commit()
        logger.warning("No handler for job type '%s' (job %d)", job.type, job.id)
        return True

    try:
        handler(db, job)
        db.refresh(job)
        job.status = JOB_STATUS_DONE
        job.progress = 100
        job.finished_at = _now()
        db.commit()
        logger.info("Job %d done", job.id)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        # Re-fetch after rollback
        job = db.get(Job, job.id)
        if job is None:
            return True

        error_text = traceback.format_exc()
        logger.error("Job %d failed: %s", job.id, exc)

        if job.attempts < MAX_JOB_ATTEMPTS:
            job.status = "queued"  # retry
            job.error = error_text[:2000]
        else:
            job.status = JOB_STATUS_FAILED
            job.error = error_text[:2000]
            job.finished_at = _now()

        db.commit()

    return True


def run_worker() -> None:
    logger.info("IdeaScope worker started (poll every %ds)", POLL_INTERVAL)
    while _running:
        processed = False
        db = SessionLocal()
        try:
            processed = _claim_and_run(db)
        except Exception:
            logger.exception("Unexpected error in worker loop")
        finally:
            db.close()

        if not processed:
            time.sleep(POLL_INTERVAL)

    logger.info("Worker stopped cleanly")


if __name__ == "__main__":
    run_worker()
