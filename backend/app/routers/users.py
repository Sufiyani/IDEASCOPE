"""
IdeaScope – User management router.
Owner: Member 2 (Sufiyaan Imran)
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin, require_main_admin
from app.schemas.users import UserCreate, UserRoleUpdate, UserStatusUpdate, UserUpdate
from app.services import user_service

router = APIRouter(tags=["Users"])


@router.get("")
def list_users(
    role: str | None = Query(None),
    is_active: bool | None = Query(None),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    actor=Depends(require_admin),
):
    return user_service.list_users(db, role, is_active, q, page, page_size)


@router.post("", status_code=201)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    actor=Depends(require_admin),
):
    return user_service.create_user(db, body.model_dump(), actor)


@router.get("/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    actor=Depends(require_admin),
):
    from app.services.auth_service import _user_to_dict

    u = user_service.get_user(db, user_id)
    return _user_to_dict(u)


@router.patch("/{user_id}")
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    actor=Depends(require_admin),
):
    return user_service.update_user(db, user_id, body.model_dump(exclude_none=True), actor)


@router.patch("/{user_id}/role")
def change_role(
    user_id: int,
    body: UserRoleUpdate,
    db: Session = Depends(get_db),
    actor=Depends(require_admin),
):
    return user_service.change_role(db, user_id, body.role, actor)


@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    db: Session = Depends(get_db),
    actor=Depends(require_admin),
):
    return user_service.reset_password(db, user_id, actor)


@router.patch("/{user_id}/status")
def set_status(
    user_id: int,
    body: UserStatusUpdate,
    db: Session = Depends(get_db),
    actor=Depends(require_main_admin),
):
    return user_service.set_status(db, user_id, body.is_active, actor)
