"""
IdeaScope – Audit log writer.
Owner: Member 2 (Sufiyaan Imran)

Adds an AuditLog row in the SAME transaction as the triggering change.
"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session


def write_audit(
    db: Session,
    actor_id: Optional[int],
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    details: Optional[Any] = None,
) -> None:
    """
    Persist a single audit log entry within the current transaction.

    Args:
        db:          SQLAlchemy session.
        actor_id:    ID of the acting user (None = system).
        action:      Dotted action label, e.g. 'user.created'.
        target_type: Optional entity type name, e.g. 'User'.
        target_id:   Optional primary key of the affected entity.
        details:     Optional dict with old/new values (stored as JSONB).
    """
    from app.models.audit_log import AuditLog

    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    db.add(entry)
    # Do NOT commit here – the caller owns the transaction boundary.
