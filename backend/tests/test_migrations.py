"""
Tests for migration correctness.
Owner: Member 2 (Sufiyaan Imran)
"""

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import InternalError


def test_all_member2_tables_exist(db):
    inspector = inspect(db.get_bind())
    tables = inspector.get_table_names()
    for expected in [
        "users",
        "refresh_tokens",
        "groups",
        "group_members",
        "categories",
        "sdgs",
        "audit_logs",
        "jobs",
    ]:
        assert expected in tables, f"Table '{expected}' missing"


def test_users_columns(db):
    inspector = inspect(db.get_bind())
    cols = {c["name"] for c in inspector.get_columns("users")}
    expected = {
        "id",
        "username",
        "full_name",
        "email",
        "roll_no",
        "password_hash",
        "role",
        "is_main_admin",
        "is_active",
        "must_change_password",
        "failed_logins",
        "locked_until",
        "last_login_at",
        "created_by",
        "created_at",
        "updated_at",
    }
    assert expected == cols


def test_jobs_columns(db):
    inspector = inspect(db.get_bind())
    cols = {c["name"] for c in inspector.get_columns("jobs")}
    expected = {
        "id",
        "type",
        "target_id",
        "status",
        "progress",
        "attempts",
        "error",
        "result",
        "created_by",
        "created_at",
        "started_at",
        "finished_at",
    }
    assert expected == cols


def test_group_members_has_no_id_column(db):
    inspector = inspect(db.get_bind())
    cols = {c["name"] for c in inspector.get_columns("group_members")}
    assert "id" not in cols
    assert "group_id" in cols
    assert "user_id" in cols


def test_12_categories_after_seed(db):
    from scripts.setup_initial_data import seed_reference_data

    seed_reference_data(db)
    result = db.execute(text("SELECT COUNT(*) FROM categories")).scalar()
    assert result == 12


def test_17_sdgs_after_seed(db):
    from scripts.setup_initial_data import seed_reference_data

    seed_reference_data(db)
    result = db.execute(text("SELECT COUNT(*) FROM sdgs")).scalar()
    assert result == 17


def test_category_names_match_seed_data(db):
    from app.core.seed_data import CATEGORY_NAMES
    from scripts.setup_initial_data import seed_reference_data

    seed_reference_data(db)
    rows = db.execute(text("SELECT id, name FROM categories ORDER BY id")).fetchall()
    for row_id, row_name in rows:
        assert CATEGORY_NAMES[row_id] == row_name


def test_sdg_names_match_seed_data(db):
    from app.core.seed_data import SDG_NAMES
    from scripts.setup_initial_data import seed_reference_data

    seed_reference_data(db)
    rows = db.execute(text("SELECT number, name FROM sdgs ORDER BY number")).fetchall()
    for number, name in rows:
        assert SDG_NAMES[number] == name


def test_second_main_admin_fails(db):
    from app.core.security import hash_password
    from app.models.user import User

    db.add(
        User(
            username="admin1",
            full_name="A1",
            password_hash=hash_password("P@ss1234"),
            role="admin",
            is_main_admin=True,
        )
    )
    db.commit()

    import sqlalchemy.exc

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db.add(
            User(
                username="admin2",
                full_name="A2",
                password_hash=hash_password("P@ss1234"),
                role="admin",
                is_main_admin=True,
            )
        )
        db.commit()

    db.rollback()


def test_main_admin_with_role_student_fails(db):
    import sqlalchemy.exc

    from app.core.security import hash_password
    from app.models.user import User

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db.add(
            User(
                username="badmin",
                full_name="Bad Admin",
                password_hash=hash_password("P@ss1234"),
                role="student",
                is_main_admin=True,
            )
        )
        db.commit()

    db.rollback()


def test_invalid_role_fails(db):
    import sqlalchemy.exc

    from app.core.security import hash_password
    from app.models.user import User

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db.add(
            User(
                username="badrole",
                full_name="Bad",
                password_hash=hash_password("P@ss1234"),
                role="superuser",
                is_main_admin=False,
            )
        )
        db.commit()

    db.rollback()


def test_audit_log_update_blocked(db):
    from app.core.security import hash_password
    from app.models.audit_log import AuditLog
    from app.models.user import User

    u = User(
        username="audituser",
        full_name="Audit",
        password_hash=hash_password("P@ss1234"),
        role="student",
    )
    db.add(u)
    db.commit()
    db.refresh(u)

    log = AuditLog(actor_id=u.id, action="test.action")
    db.add(log)
    db.commit()
    db.refresh(log)

    with pytest.raises(InternalError):
        db.execute(text(f"UPDATE audit_logs SET action='hacked' WHERE id={log.id}"))
        db.commit()

    db.rollback()


def test_audit_log_delete_blocked(db):
    from app.core.security import hash_password
    from app.models.audit_log import AuditLog
    from app.models.user import User

    u = User(
        username="delaudit",
        full_name="Del",
        password_hash=hash_password("P@ss1234"),
        role="student",
    )
    db.add(u)
    db.commit()
    db.refresh(u)

    log = AuditLog(actor_id=u.id, action="del.test")
    db.add(log)
    db.commit()
    db.refresh(log)

    with pytest.raises(InternalError):
        db.execute(text(f"DELETE FROM audit_logs WHERE id={log.id}"))
        db.commit()

    db.rollback()

    db.rollback()
