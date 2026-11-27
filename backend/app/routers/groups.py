"""
IdeaScope – Group management router.
Owner: Member 2 (Sufiyaan Imran)
"""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.schemas.groups import AddMemberRequest, GroupCreate
from app.services import group_service

router = APIRouter(tags=["Groups"])


@router.post("", status_code=201)
def create_group(
    body: GroupCreate,
    db: Session = Depends(get_db),
    actor=Depends(get_current_user),
):
    return group_service.create_group(db, body.name, actor)


@router.get("/me")
def get_my_group(
    db: Session = Depends(get_db),
    actor=Depends(get_current_user),
):
    return group_service.get_my_group(db, actor)


@router.post("/{group_id}/members", status_code=201)
def add_member(
    group_id: int,
    body: AddMemberRequest,
    db: Session = Depends(get_db),
    actor=Depends(get_current_user),
):
    return group_service.add_member(db, group_id, body.user_id, actor)


@router.delete("/{group_id}/members/{user_id}", status_code=204)
def remove_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    actor=Depends(get_current_user),
):
    group_service.remove_member(db, group_id, user_id, actor)
    return Response(status_code=204)


@router.get("")
def list_groups(
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    actor=Depends(require_admin),
):
    return group_service.list_groups(db, q, page, page_size)


@router.get("/{group_id}")
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    actor=Depends(get_current_user),
):
    return group_service.get_group(db, group_id, actor)
