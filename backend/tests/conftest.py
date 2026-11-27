"""
IdeaScope – pytest configuration and fixtures.
Owner: Member 2 (Sufiyaan Imran)

Uses a SEPARATE database <POSTGRES_DB>_test so the dev DB is never touched.
"""

from __future__ import annotations

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.orm import sessionmaker

from alembic import command
from app.core.config import settings
from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from scripts.setup_initial_data import seed_reference_data

# ── Build test DB URL ─────────────────────────────────────────────────────────


def _test_url() -> str:
    base = make_url(settings.database_url)
    return str(base.set(database=base.database + "_test"))


TEST_DB_URL = _test_url()
_test_engine = None
_TestSession = None


# ── Session-scoped DB setup ───────────────────────────────────────────────────


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    global _test_engine, _TestSession

    base_url = make_url(settings.database_url)
    maint_url = str(base_url.set(database="postgres"))
    test_db = base_url.database + "_test"

    # Connect to postgres maintenance db to drop/create the test database
    maint_engine = create_engine(maint_url, isolation_level="AUTOCOMMIT")
    try:
        with maint_engine.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{test_db}" WITH (FORCE)'))
            conn.execute(text(f'CREATE DATABASE "{test_db}"'))
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"Cannot connect to database: {e}")
    finally:
        maint_engine.dispose()

    # Run real Alembic migrations against the test DB
    alembic_cfg = Config("alembic.ini")
    # Escape % as %% for ConfigParser
    escaped_url = TEST_DB_URL.replace("%", "%%")
    alembic_cfg.set_main_option("sqlalchemy.url", escaped_url)
    command.upgrade(alembic_cfg, "head")

    _test_engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
    _TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

    yield

    _test_engine.dispose()


# ── Function-scoped: truncate tables and re-seed between tests ────────────────


@pytest.fixture(autouse=True)
def clean_db(setup_test_database):
    db = _TestSession()
    try:
        # TRUNCATE all Member 2 tables (order respects FKs)
        db.execute(text("TRUNCATE audit_logs RESTART IDENTITY CASCADE"))
        db.execute(text("TRUNCATE group_members CASCADE"))
        db.execute(text("TRUNCATE groups RESTART IDENTITY CASCADE"))
        db.execute(text("TRUNCATE refresh_tokens RESTART IDENTITY CASCADE"))
        db.execute(text("TRUNCATE jobs RESTART IDENTITY CASCADE"))
        db.execute(text("TRUNCATE users RESTART IDENTITY CASCADE"))
        db.commit()
        seed_reference_data(db)
    finally:
        db.close()


# ── Override get_db dependency ────────────────────────────────────────────────


@pytest.fixture
def db():
    session = _TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def override_get_db(setup_test_database):
    def _override():
        s = _TestSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.pop(get_db, None)


# ── HTTP test client ──────────────────────────────────────────────────────────


@pytest.fixture
def client():
    from httpx import ASGITransport, Client

    with Client(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ── User creation helpers ─────────────────────────────────────────────────────


def _make_user(db, **kwargs):
    from app.models.user import User

    defaults = {
        "username": "testuser",
        "full_name": "Test User",
        "password_hash": hash_password("Password1"),
        "role": "student",
        "is_main_admin": False,
        "is_active": True,
        "must_change_password": False,
    }
    defaults.update(kwargs)
    u = User(**defaults)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def student_user(db):
    return _make_user(
        db,
        username="2023f-bse-001",
        full_name="Student One",
        roll_no="2023F-BSE-001",
        role="student",
    )


@pytest.fixture
def admin_user(db):
    return _make_user(
        db,
        username="adminuser",
        full_name="Admin User",
        role="admin",
    )


@pytest.fixture
def main_admin_user(db):
    return _make_user(
        db,
        username="admin",
        full_name="Main Admin",
        email="admin@test.com",
        role="admin",
        is_main_admin=True,
    )


def _login(client, username: str, password: str = "Password1") -> dict:
    r = client.post("/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture
def student_token(client, student_user):
    return _login(client, student_user.username)["access_token"]


@pytest.fixture
def admin_token(client, admin_user):
    return _login(client, admin_user.username)["access_token"]


@pytest.fixture
def main_admin_token(client, main_admin_user):
    return _login(client, main_admin_user.username)["access_token"]
