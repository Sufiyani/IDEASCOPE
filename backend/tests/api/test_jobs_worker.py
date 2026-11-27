"""
Tests for jobs endpoint and worker logic.
Owner: Member 2 (Sufiyaan Imran)
"""

import pytest
from fastapi import HTTPException

from app.core.constants import JOB_STATUS_DONE, JOB_STATUS_FAILED, MAX_JOB_ATTEMPTS
from app.worker.queue import enqueue_job
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
    with pytest.raises(HTTPException):
        enqueue_job(db, "not_a_real_type", target_id=1)


def test_get_job_as_creator(client, db, student_user, student_token):
    job = enqueue_job(db, "process_abstract", target_id=1, created_by=student_user.id)
    db.commit()
    r = client.get(f"/jobs/{job.id}", headers=_auth(student_token))
    assert r.status_code == 200
    assert r.json()["id"] == job.id


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


def test_worker_runs_fake_handler(db, student_user, monkeypatch):
    """Patch runner module's get_handler directly so the import is replaced."""
    call_log = []

    def fake_handler(db, job):
        call_log.append(job.id)
        job.result = {"done": True}

    monkeypatch.setattr("app.worker.runner.get_handler", lambda t: fake_handler)

    job = enqueue_job(db, "process_abstract", target_id=1, created_by=student_user.id)
    db.commit()

    processed = _claim_and_run(db)
    assert processed is True
    db.refresh(job)
    assert job.status == JOB_STATUS_DONE
    assert job.id in call_log


def test_worker_retries_then_fails(db, student_user, monkeypatch):
    fail_count = [0]

    def failing_handler(db, job):
        fail_count[0] += 1
        raise RuntimeError("simulated failure")

    monkeypatch.setattr("app.worker.runner.get_handler", lambda t: failing_handler)

    job = enqueue_job(db, "process_abstract", target_id=1, created_by=student_user.id)
    db.commit()

    for attempt in range(1, MAX_JOB_ATTEMPTS + 1):
        processed = _claim_and_run(db)
        assert processed is True
        db.refresh(job)
        if attempt < MAX_JOB_ATTEMPTS:
            assert job.status == "queued"
        else:
            assert job.status == JOB_STATUS_FAILED

    assert fail_count[0] == MAX_JOB_ATTEMPTS


def test_worker_missing_handler_fails_immediately(db, student_user, monkeypatch):
    monkeypatch.setattr("app.worker.runner.get_handler", lambda t: None)

    job = enqueue_job(db, "process_abstract", target_id=1, created_by=student_user.id)
    db.commit()

    _claim_and_run(db)
    db.refresh(job)
    assert job.status == JOB_STATUS_FAILED
    assert job.error == "no_handler_registered"
