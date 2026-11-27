"""
IdeaScope – User management service.
Owner: Member 2 (Sufiyaan Imran)
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.constants import ROLE_ADMIN, ROLE_STUDENT
from app.core.security import generate_temp_password, hash_password
from app.models.group import GroupMember
from app.models.user import User
from app.services.auth_service import _revoke_all_tokens, _user_to_dict


def _now() -> datetime:
    return datetime.now(UTC)


def _check_uniqueness(
    db: Session,
    username: str | None = None,
    email: str | None = None,
    roll_no: str | None = None,
    exclude_id: int | None = None,
) -> None:
    if username:
        q = select(User).where(User.username == username)
        if exclude_id:
            q = q.where(User.id != exclude_id)
        if db.scalar(q):
            raise HTTPException(status_code=409, detail="username_already_exists")

    if email:
        q = select(User).where(User.email == email)
        if exclude_id:
            q = q.where(User.id != exclude_id)
        if db.scalar(q):
            raise HTTPException(status_code=409, detail="email_already_exists")

    if roll_no:
        q = select(User).where(User.roll_no == roll_no)
        if exclude_id:
            q = q.where(User.id != exclude_id)
        if db.scalar(q):
            raise HTTPException(status_code=409, detail="roll_no_already_exists")


def list_users(
    db: Session,
    role: str | None,
    is_active: bool | None,
    q: str | None,
    page: int,
    page_size: int,
) -> dict:
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                User.username.ilike(like),
                User.full_name.ilike(like),
                User.email.ilike(like),
                User.roll_no.ilike(like),
            )
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    users = db.scalars(stmt.order_by(User.id).offset((page - 1) * page_size).limit(page_size)).all()
    return {
        "items": [_user_to_dict(u) for u in users],
        "total": total or 0,
        "page": page,
        "page_size": page_size,
    }


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    return user


def create_user(db: Session, data: dict, actor: User) -> dict:
    role = data.get("role", ROLE_STUDENT)
    full_name = data["full_name"]
    email = data.get("email")
    roll_no = data.get("roll_no")
    given_username = data.get("username")
    password = data.get("password")

    if role == ROLE_STUDENT:
        if not roll_no:
            raise HTTPException(status_code=400, detail="roll_no_required_for_student")
        username = roll_no.lower()
    else:
        if not given_username:
            raise HTTPException(status_code=400, detail="username_required_for_admin")
        username = given_username

    _check_uniqueness(db, username=username, email=email, roll_no=roll_no)

    temp_password = None
    if password is None:
        temp_password = generate_temp_password()
        password = temp_password

    user = User(
        username=username,
        full_name=full_name,
        email=email,
        roll_no=roll_no,
        password_hash=hash_password(password),
        role=role,
        is_main_admin=False,
        must_change_password=True,
        created_by=actor.id,
    )
    db.add(user)
    db.flush()  # get user.id before audit

    write_audit(db, actor.id, "user.created", "User", user.id, {"username": username, "role": role})
    db.commit()
    db.refresh(user)

    return {"user": _user_to_dict(user), "temporary_password": temp_password}


def update_user(db: Session, user_id: int, data: dict, actor: User) -> dict:
    user = get_user(db, user_id)

    # Main admin account can only be edited by the main admin himself
    if user.is_main_admin and not actor.is_main_admin:
        raise HTTPException(status_code=403, detail="main_admin_protected")

    old = {k: getattr(user, k) for k in ("full_name", "email", "roll_no", "username")}

    if "full_name" in data and data["full_name"] is not None:
        user.full_name = data["full_name"]

    new_email = data.get("email")
    if new_email is not None:
        _check_uniqueness(db, email=new_email, exclude_id=user_id)
        user.email = new_email

    new_roll_no = data.get("roll_no")
    if new_roll_no is not None:
        _check_uniqueness(db, roll_no=new_roll_no, exclude_id=user_id)
        user.roll_no = new_roll_no
        if user.role == ROLE_STUDENT:
            new_username = new_roll_no.lower()
            _check_uniqueness(db, username=new_username, exclude_id=user_id)
            user.username = new_username

    new = {k: getattr(user, k) for k in ("full_name", "email", "roll_no", "username")}
    write_audit(db, actor.id, "user.updated", "User", user_id, {"old": old, "new": new})
    db.commit()
    db.refresh(user)
    return _user_to_dict(user)


def change_role(db: Session, user_id: int, new_role: str, actor: User) -> dict:
    user = get_user(db, user_id)

    if user.is_main_admin:
        raise HTTPException(status_code=403, detail="main_admin_protected")
    if user.id == actor.id:
        raise HTTPException(status_code=403, detail="cannot_change_own_role")

    if new_role == ROLE_ADMIN and user.role == ROLE_STUDENT:
        # Check if student is in a group
        gm = db.scalar(select(GroupMember).where(GroupMember.user_id == user_id))
        if gm:
            raise HTTPException(status_code=409, detail="user_in_group")

    if new_role == ROLE_STUDENT and user.role == ROLE_ADMIN and not user.roll_no:
        raise HTTPException(status_code=409, detail="roll_no_required")

    old_role = user.role
    user.role = new_role
    write_audit(
        db,
        actor.id,
        "user.role_changed",
        "User",
        user_id,
        {"old_role": old_role, "new_role": new_role},
    )
    db.commit()
    db.refresh(user)
    return _user_to_dict(user)


def reset_password(db: Session, user_id: int, actor: User) -> dict:
    if user_id == actor.id:
        raise HTTPException(status_code=400, detail="use_change_password")

    user = get_user(db, user_id)

    if user.is_main_admin:
        raise HTTPException(status_code=403, detail="main_admin_protected")

    temp = generate_temp_password()
    user.password_hash = hash_password(temp)
    user.must_change_password = True
    user.failed_logins = 0
    user.locked_until = None

    _revoke_all_tokens(db, user_id)

    write_audit(db, actor.id, "user.password_reset", "User", user_id)
    db.commit()
    return {"temporary_password": temp}


def set_status(db: Session, user_id: int, is_active: bool, actor: User) -> dict:
    if user_id == actor.id:
        raise HTTPException(status_code=403, detail="main_admin_protected")

    user = get_user(db, user_id)

    if user.is_main_admin:
        raise HTTPException(status_code=403, detail="main_admin_protected")

    user.is_active = is_active

    if not is_active:
        _revoke_all_tokens(db, user_id)
    else:
        user.failed_logins = 0
        user.locked_until = None

    action = "user.activated" if is_active else "user.deactivated"
    write_audit(db, actor.id, action, "User", user_id)
    db.commit()
    db.refresh(user)
    return _user_to_dict(user)
