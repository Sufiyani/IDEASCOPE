"""
Tests for jobs endpoint and worker logic.
Owner: Member 2 (Sufiyaan Imran)
"""

import pytest

from app.core.constants import JOB_STATUS_DONE, JOB_STATUS_FAILED, MAX_JOB_ATTEMPTS
from app.worker.queue import enqueue_job
from app.worker.registry import get_handler
from app.worker.runner import _claim_and_run


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_enqueue_job(db, student_user):
    job = enqueue_job(db, "process_abstract", target_id=1, created_by=student_user.id)
    db.commit()
    assert job.id is not None
    assert job.status == "queued"
    assert job.type == "process_abstract"


def test_invalid_job_type(db):
    with pytest.raises(Exception):
        enqueue_job(db, "not_a_real_type", target_id=1)


def test_get_job_as_creator(client, db, student_user, student_token):
    job = enqueue_job(db, "process_abstract", target_id=1, created_by=student_user.id)
    db.commit()

    r = client.get(f"/jobs/{job.id}", headers=_auth(student_token))
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == job.id
    assert data["type"] == "process_abstract"


def test_get_job_forbidden_other_user(client, db, student_user, admin_user, student_token):
    job = enqueue_job(db, "process_abstract", target_id=1, created_by=admin_user.id)
    db.commit()

    r = client.get(f"/jobs/{job.id}", headers=_auth(student_token))
    assert r.status_code == 403


def test_get_job_admin_can_see_any(client, db, student_user, admin_token):
    job = enqueue_job(db, "process_abstract", target_id=1, created_by=student_user.id)
    db.commit()

    r = client.get(f"/jobs/{job.id}", headers=_auth(admin_token))
    assert r.status_code == 200


def test_worker_runs_fake_handler(db, student_user):
    """Register a fake handler, run a job cycle, verify it completes."""
    from app.worker import registry

    call_log = []

    def fake_handler(db, job):
        call_log.append(job.id)
        job.result = {"done": True}

    original = registry.get_handler

    def patched_get_handler(job_type):
        if job_type == "process_abstract":
            return fake_handler
        return original(job_type)

    registry.get_handler = patched_get_handler

    try:
        job = enqueue_job(db, "process_abstract", target_id=1, created_by=student_user.id)
        db.commit()

        processed = _claim_and_run(db)
        assert processed is True
        db.refresh(job)
        assert job.status == JOB_STATUS_DONE
        assert job.id in call_log
    finally:
        registry.get_handler = original


def test_worker_retries_then_fails(db, student_user):
    from app.worker import registry

    fail_count = [0]

    def failing_handler(db, job):
        fail_count[0] += 1
        raise RuntimeError("simulated failure")

    original = registry.get_handler

    def patched(job_type):
        if job_type == "process_abstract":
            return failing_handler
        return original(job_type)

    registry.get_handler = patched

    try:
        job = enqueue_job(db, "process_abstract", target_id=1, created_by=student_user.id)
        db.commit()

        # Run MAX_JOB_ATTEMPTS times; each time the job goes back to queued
        for attempt in range(1, MAX_JOB_ATTEMPTS + 1):
            processed = _claim_and_run(db)
            assert processed is True
            db.refresh(job)
            if attempt < MAX_JOB_ATTEMPTS:
                assert job.status == "queued"
            else:
                assert job.status == JOB_STATUS_FAILED

        assert fail_count[0] == MAX_JOB_ATTEMPTS
    finally:
        registry.get_handler = patched


def test_worker_missing_handler_fails_immediately(db, student_user):
    job = enqueue_job(db, "process_abstract", target_id=1, created_by=student_user.id)
    db.commit()

    from app.worker import registry

    original = registry.get_handler
    registry.get_handler = lambda t: None

    try:
        _claim_and_run(db)
        db.refresh(job)
        assert job.status == JOB_STATUS_FAILED
        assert job.error == "no_handler_registered"
    finally:
        registry.get_handler = original
