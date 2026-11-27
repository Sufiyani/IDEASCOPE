"""
IdeaScope – Group management service.
Owner: Member 2 (Sufiyaan Imran)
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.constants import DEFAULT_MAX_GROUP_SIZE, ROLE_STUDENT
from app.models.group import Group, GroupMember
from app.models.user import User


def _now() -> datetime:
    return datetime.now(UTC)


def _get_max_group_size(db: Session) -> int:
    """Read max_group_size from settings table if it exists; fall back to default."""
    try:
        with db.begin_nested():
            from sqlalchemy import text

            row = db.execute(
                text("SELECT value FROM settings WHERE key = 'max_group_size' LIMIT 1")
            ).fetchone()
            if row:
                return int(row[0])
    except SQLAlchemyError:
        pass
    return DEFAULT_MAX_GROUP_SIZE


def _member_count(db: Session, group_id: int) -> int:
    return db.scalar(select(func.count()).where(GroupMember.group_id == group_id)) or 0


def _build_group_out(db: Session, group: Group) -> dict:
    members_rows = db.execute(
        select(GroupMember, User)
        .join(User, User.id == GroupMember.user_id)
        .where(GroupMember.group_id == group.id)
        .order_by(GroupMember.joined_at)
    ).all()

    members = []
    for gm, u in members_rows:
        members.append(
            {
                "user_id": u.id,
                "full_name": u.full_name,
                "username": u.username,
                "roll_no": u.roll_no,
                "email": u.email,
                "joined_at": gm.joined_at.isoformat() if gm.joined_at else None,
                "is_leader": u.id == group.leader_id,
            }
        )

    return {
        "id": group.id,
        "name": group.name,
        "batch": group.batch,
        "leader_id": group.leader_id,
        "created_at": group.created_at.isoformat() if group.created_at else None,
        "members": members,
    }


def create_group(db: Session, name: str, actor: User) -> dict:
    if actor.role != ROLE_STUDENT:
        raise HTTPException(status_code=403, detail="forbidden")

    if not actor.roll_no:
        raise HTTPException(status_code=400, detail="roll_no_required")

    # Student must not already be in a group
    existing = db.scalar(select(GroupMember).where(GroupMember.user_id == actor.id))
    if existing:
        raise HTTPException(status_code=409, detail="already_in_group")

    batch = actor.roll_no.split("-")[0]

    group = Group(name=name, batch=batch, leader_id=actor.id)
    db.add(group)
    db.flush()

    member = GroupMember(group_id=group.id, user_id=actor.id)
    db.add(member)
    db.commit()
    db.refresh(group)
    return _build_group_out(db, group)


def get_my_group(db: Session, actor: User) -> dict:
    gm = db.scalar(select(GroupMember).where(GroupMember.user_id == actor.id))
    if gm is None:
        raise HTTPException(status_code=404, detail="no_group")
    group = db.get(Group, gm.group_id)
    return _build_group_out(db, group)


def add_member(db: Session, group_id: int, target_user_id: int | None, actor: User) -> dict:
    group = db.get(Group, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="group_not_found")

    # Determine who is being added
    if target_user_id is None:
        target_user_id = actor.id

    # Permission check: actor must be the student themselves, the leader, or an admin
    is_self = target_user_id == actor.id
    is_leader = group.leader_id == actor.id
    is_admin = actor.role != ROLE_STUDENT

    if not (is_self or is_leader or is_admin):
        raise HTTPException(status_code=403, detail="forbidden")

    target = db.get(User, target_user_id)
    if target is None or not target.is_active or target.role != ROLE_STUDENT:
        raise HTTPException(status_code=409, detail="not_a_student")

    existing = db.scalar(select(GroupMember).where(GroupMember.user_id == target_user_id))
    if existing:
        raise HTTPException(status_code=409, detail="already_in_group")

    max_size = _get_max_group_size(db)
    if _member_count(db, group_id) >= max_size:
        raise HTTPException(status_code=409, detail="group_full")

    member = GroupMember(group_id=group_id, user_id=target_user_id)
    db.add(member)
    db.commit()
    db.refresh(group)
    return _build_group_out(db, group)


def remove_member(db: Session, group_id: int, user_id: int, actor: User) -> None:
    group = db.get(Group, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="group_not_found")

    gm = db.scalar(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    )
    if gm is None:
        raise HTTPException(status_code=404, detail="not_a_member")

    # Permission
    is_self = user_id == actor.id
    is_leader = group.leader_id == actor.id
    is_admin = actor.role != ROLE_STUDENT

    if not (is_self or is_leader or is_admin):
        raise HTTPException(status_code=403, detail="forbidden")

    db.delete(gm)
    db.flush()

    remaining = db.scalars(
        select(GroupMember).where(GroupMember.group_id == group_id).order_by(GroupMember.joined_at)
    ).all()

    if not remaining:
        # Last member left – delete the group
        try:
            db.delete(group)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="group_has_proposals")
    else:
        # Transfer leadership if the leader left
        if group.leader_id == user_id:
            group.leader_id = remaining[0].user_id
        db.commit()


def list_groups(
    db: Session,
    q: str | None,
    page: int,
    page_size: int,
) -> dict:
    stmt = select(Group)
    if q:
        stmt = stmt.where(Group.name.ilike(f"%{q}%"))

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    groups = db.scalars(
        stmt.order_by(Group.id).offset((page - 1) * page_size).limit(page_size)
    ).all()

    items = []
    for g in groups:
        items.append(
            {
                "id": g.id,
                "name": g.name,
                "batch": g.batch,
                "leader_id": g.leader_id,
                "created_at": g.created_at.isoformat() if g.created_at else None,
                "member_count": _member_count(db, g.id),
            }
        )

    return {"items": items, "total": total or 0, "page": page, "page_size": page_size}


def get_group(db: Session, group_id: int, actor: User) -> dict:
    group = db.get(Group, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="group_not_found")

    is_admin = actor.role != ROLE_STUDENT
    is_member = (
        db.scalar(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == actor.id,
            )
        )
        is not None
    )

    if not (is_admin or is_member):
        raise HTTPException(status_code=403, detail="forbidden")

    return _build_group_out(db, group)
