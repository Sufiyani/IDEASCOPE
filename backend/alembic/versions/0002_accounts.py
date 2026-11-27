"""Accounts: users, refresh_tokens, groups, group_members, audit_logs

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-01 00:01:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("roll_no", sa.Text(), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("is_main_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "must_change_password", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column("failed_logins", sa.SmallInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("role IN ('student', 'admin')", name="ck_users_role"),
        sa.CheckConstraint(
            "NOT is_main_admin OR role = 'admin'",
            name="ck_users_main_admin_must_be_admin",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("roll_no", name="uq_users_roll_no"),
    )

    # Partial unique index: only one main admin
    op.create_index(
        "ix_users_is_main_admin_partial",
        "users",
        ["is_main_admin"],
        unique=True,
        postgresql_where=sa.text("is_main_admin = true"),
    )
    op.create_index("ix_users_created_by", "users", ["created_by"])

    # ── refresh_tokens ────────────────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    # ── groups ────────────────────────────────────────────────────────────────
    op.create_table(
        "groups",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("batch", sa.Text(), nullable=False),
        sa.Column("leader_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["leader_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_groups_leader_id", "groups", ["leader_id"])

    # ── group_members ─────────────────────────────────────────────────────────
    op.create_table(
        "group_members",
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("group_id", "user_id", name="pk_group_members"),
        sa.UniqueConstraint("user_id", name="uq_group_members_user_id"),
    )
    op.create_index("ix_group_members_group_id", "group_members", ["group_id"])

    # ── audit_logs ────────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("actor_id", sa.BigInteger(), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=True),
        sa.Column("target_id", sa.BigInteger(), nullable=True),
        sa.Column("details", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index(
        "ix_audit_logs_target_type_target_id",
        "audit_logs",
        ["target_type", "target_id"],
    )

    # ── audit_logs immutability trigger ──────────────────────────────────────
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_logs_immutable()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'audit_logs rows are immutable';
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_logs_immutable
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION audit_logs_immutable();
        """
    )


def downgrade() -> None:
    # Remove trigger and function first
    op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_immutable ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS audit_logs_immutable()")

    op.drop_index("ix_audit_logs_target_type_target_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_group_members_group_id", table_name="group_members")
    op.drop_table("group_members")

    op.drop_index("ix_groups_leader_id", table_name="groups")
    op.drop_table("groups")

    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("ix_users_is_main_admin_partial", table_name="users")
    op.drop_index("ix_users_created_by", table_name="users")
    op.drop_table("users")
