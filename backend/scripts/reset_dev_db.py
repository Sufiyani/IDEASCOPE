"""
IdeaScope – Development database reset script.
Owner: Member 2 (Sufiyaan Imran)

DANGER: Drops and recreates the public schema.
Only allowed against db / localhost / 127.0.0.1.

Run as: python -m scripts.reset_dev_db --yes
"""

from __future__ import annotations

import sys

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.exc import OperationalError


def main() -> None:
    if "--yes" not in sys.argv:
        print("ERROR: pass --yes to confirm you want to wipe the database")
        sys.exit(1)

    from app.core.config import settings

    url = make_url(settings.database_url)
    host = url.host or ""
    if host not in ("db", "localhost", "127.0.0.1"):
        print(f"ERROR: Refusing to reset database on host '{host}'. Only db/localhost/127.0.0.1 allowed.")
        sys.exit(1)

    print(f"=== Resetting database on {host} ===")

    # Connect to the postgres maintenance DB to drop/create the target DB
    maint_url = url.set(database="postgres")
    maint_engine = create_engine(maint_url.render_as_string(hide_password=False), isolation_level="AUTOCOMMIT")

    db_name = url.database
    try:
        with maint_engine.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)'))
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
        print(f"  [ok] dropped and recreated database '{db_name}'")
    except OperationalError as e:
        print(f"ERROR connecting to postgres maintenance DB: {e}")
        sys.exit(1)
    finally:
        maint_engine.dispose()

    # Run alembic migrations
    print("\n-- Running alembic upgrade head --")
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(cfg, "head")
    print("  [ok] migrations applied")

    # Run setup script
    print("\n-- Running setup_initial_data --")
    from app.core.database import SessionLocal
    from scripts.setup_initial_data import create_main_admin, seed_reference_data

    db = SessionLocal()
    try:
        seed_reference_data(db)
        create_main_admin(db)
    finally:
        db.close()

    # Member 3 hook: add past project seed data import here
    # e.g. from scripts.seed_past_projects import seed_2022f; seed_2022f(db)

    print("\n=== Reset complete ===")


if __name__ == "__main__":
    main()
