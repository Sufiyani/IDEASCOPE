"""
IdeaScope – Group schemas.
Owner: Member 2 (Sufiyaan Imran)
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class GroupCreate(BaseModel):
    name: str


class AddMemberRequest(BaseModel):
    user_id: int | None = None


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    full_name: str
    username: str
    roll_no: str | None
    email: str | None
    joined_at: str
    is_leader: bool


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    batch: str
    leader_id: int
    created_at: str
    members: list[MemberOut] = []


class GroupListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    batch: str
    leader_id: int
    created_at: str
    member_count: int


class PaginatedGroups(BaseModel):
    items: list[GroupListItem]
    total: int
    page: int
    page_size: int
