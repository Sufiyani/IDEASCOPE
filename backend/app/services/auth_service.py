"""
IdeaScope – Authentication service.
Owner: Member 2 (Sufiyaan Imran)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.constants import LOCK_MINUTES, MAX_FAILED_LOGINS
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User


def _now() -> datetime:
    return datetime.now(UTC)


def _build_token_response(db: Session, user: User) -> dict:
    """Create a new token pair, store hashed refresh token, return dict."""
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)

    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh),
        expires_at=_now() + timedelta(days=7),
    )
    db.add(rt)
    # Caller commits

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "must_change_password": user.must_change_password,
        "user": _user_to_dict(user),
    }


def _user_to_dict(user: User) -> dict:
    def _fmt(dt):
        return dt.isoformat() if dt else None

    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "roll_no": user.roll_no,
        "role": user.role,
        "is_main_admin": user.is_main_admin,
        "is_active": user.is_active,
        "must_change_password": user.must_change_password,
        "locked_until": _fmt(user.locked_until),
        "last_login_at": _fmt(user.last_login_at),
        "created_by": user.created_by,
        "created_at": _fmt(user.created_at),
        "updated_at": _fmt(user.updated_at),
    }


def login(db: Session, username: str, password: str) -> dict:
    """Authenticate user; return token response dict."""
    user = db.scalar(select(User).where(User.username == username))

    # Always check lockout before credential check
    if user and user.locked_until and user.locked_until > _now():
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="account_locked")

    if user is None or not verify_password(password, user.password_hash):
        if user is not None:
            user.failed_logins = (user.failed_logins or 0) + 1
            if user.failed_logins >= MAX_FAILED_LOGINS:
                user.locked_until = _now() + timedelta(minutes=LOCK_MINUTES)
                user.failed_logins = 0
            db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    # Correct password but still locked (edge: set while counting)
    if user.locked_until and user.locked_until > _now():
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="account_locked")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="account_deactivated")

    user.failed_logins = 0
    user.locked_until = None
    user.last_login_at = _now()

    result = _build_token_response(db, user)
    db.commit()
    return result


def refresh_tokens(db: Session, raw_token: str) -> dict:
    """Rotate refresh token; return new token pair."""
    from app.core.security import decode_token

    payload = decode_token(raw_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token"
        )

    h = hash_token(raw_token)
    rt = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == h))

    if rt is None or rt.revoked_at is not None or rt.expires_at < _now():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token"
        )

    user = db.get(User, rt.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token"
        )

    # Revoke old token
    rt.revoked_at = _now()

    result = _build_token_response(db, user)
    db.commit()
    return result


def logout(db: Session, raw_token: str) -> None:
    """Revoke a refresh token. Always succeeds (204)."""
    h = hash_token(raw_token)
    rt = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == h))
    if rt and rt.revoked_at is None:
        rt.revoked_at = _now()
        db.commit()


def change_password(db: Session, user: User, current_password: str, new_password: str) -> dict:
    """Verify current password, set new, revoke all tokens, return new pair."""
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="wrong_current_password"
        )

    if verify_password(new_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="new_password_same_as_current",
        )

    user.password_hash = hash_password(new_password)
    user.must_change_password = False

    # Revoke all refresh tokens for this user
    _revoke_all_tokens(db, user.id)

    write_audit(db, user.id, "user.password_changed", "User", user.id)

    result = _build_token_response(db, user)
    db.commit()
    return result


def _revoke_all_tokens(db: Session, user_id: int) -> None:
    """Mark all non-revoked refresh tokens for a user as revoked."""
    tokens = db.scalars(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
    ).all()
    now = _now()
    for t in tokens:
        t.revoked_at = now
