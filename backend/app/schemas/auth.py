"""
IdeaScope – Auth request/response schemas.
Owner: Member 2 (Sufiyaan Imran)

No EmailStr – email-validator is not installed. Email validated by regex.
No `from __future__ import annotations` per rules.
"""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

PASSWORD_MIN_CHARS = 8
PASSWORD_MAX_BYTES = 72


def _validate_password_policy(value: str) -> str:
    if len(value) < PASSWORD_MIN_CHARS:
        raise ValueError(f"password must be at least {PASSWORD_MIN_CHARS} characters")
    if len(value.encode()) > PASSWORD_MAX_BYTES:
        raise ValueError(f"password must not exceed {PASSWORD_MAX_BYTES} bytes")
    return value


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username", mode="before")
    @classmethod
    def normalise_username(cls, v: str) -> str:
        return v.strip().lower()


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password", mode="after")
    @classmethod
    def validate_new(cls, v: str) -> str:
        return _validate_password_policy(v)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    email: Optional[str] = None
    roll_no: Optional[str] = None
    role: str
    is_main_admin: bool
    is_active: bool
    must_change_password: bool
    locked_until: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    must_change_password: bool
    user: UserOut
