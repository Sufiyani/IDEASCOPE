"""
IdeaScope – Alembic environment.
Owner: Member 2 (Sufiyaan Imran)

Reads the database URL from the environment (via core/config.py) so that
alembic.ini never contains a real URL.  Tests override it by calling
config.set_main_option before running upgrade().
"""

from __future__ import annotations

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

import app.models  # noqa: F401 – ensures all metadata is loaded
from alembic import context
from app.core.config import settings

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use the SQLAlchemy metadata from our models
from app.models.base import Base

target_metadata = Base.metadata


def _get_url() -> str:
    """Return URL from alembic.ini if set, else from app settings."""
    ini_url = config.get_main_option("sqlalchemy.url")
    if ini_url:
        return ini_url
    return settings.database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generate SQL script)."""
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = _get_url()

    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
