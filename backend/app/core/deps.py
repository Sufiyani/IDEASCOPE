"""
IdeaScope – FastAPI dependency injection helpers.
Owner: Member 2 (Sufiyaan Imran)
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _get_user_from_token(token: str, db: Session):
    """Shared logic: decode token and load the active user."""
    from app.models.user import User

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token")

    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token")

    return user


def get_current_user_any(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Valid access token; user exists and is_active.
    Does NOT block on must_change_password.
    Used by /auth/me, /auth/change-password, /auth/logout.
    """
    return _get_user_from_token(token, db)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Valid access token; user exists and is_active.
    Raises 403 password_change_required when must_change_password is True.
    """
    user = _get_user_from_token(token, db)
    if user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="password_change_required",
        )
    return user


def require_admin(user=Depends(get_current_user)):
    """Allow only users with role == 'admin'."""
    from app.core.constants import ROLE_ADMIN

    if user.role != ROLE_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return user


def require_main_admin(user=Depends(get_current_user)):
    """Allow only the main admin."""
    if not user.is_main_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return user


def require_student(user=Depends(get_current_user)):
    """Allow only students."""
    from app.core.constants import ROLE_STUDENT

    if user.role != ROLE_STUDENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return user
