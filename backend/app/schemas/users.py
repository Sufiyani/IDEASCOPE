"""
IdeaScope – User management schemas.
Owner: Member 2 (Sufiyaan Imran)
"""

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.auth import PASSWORD_MAX_BYTES, PASSWORD_MIN_CHARS, UserOut  # noqa: F401

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    v = v.strip().lower()
    if v and not _EMAIL_RE.match(v):
        raise ValueError("invalid email format")
    return v or None


class UserCreate(BaseModel):
    full_name: str
    role: str = "student"
    roll_no: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

    @field_validator("full_name", mode="before")
    @classmethod
    def strip_full_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("role", mode="after")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("student", "admin"):
            raise ValueError("role must be student or admin")
        return v

    @field_validator("roll_no", mode="before")
    @classmethod
    def normalise_roll_no(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip().upper()
        return v or None

    @field_validator("username", mode="before")
    @classmethod
    def normalise_username(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip().lower()
        return v or None

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v: Optional[str]) -> Optional[str]:
        return _validate_email(v)

    @field_validator("password", mode="after")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if len(v) < PASSWORD_MIN_CHARS:
            raise ValueError(f"password must be at least {PASSWORD_MIN_CHARS} characters")
        if len(v.encode()) > PASSWORD_MAX_BYTES:
            raise ValueError(f"password must not exceed {PASSWORD_MAX_BYTES} bytes")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    roll_no: Optional[str] = None

    @field_validator("full_name", mode="before")
    @classmethod
    def strip_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return v.strip() or None

    @field_validator("roll_no", mode="before")
    @classmethod
    def normalise_roll_no(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return v.strip().upper() or None

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v: Optional[str]) -> Optional[str]:
        return _validate_email(v)


class UserRoleUpdate(BaseModel):
    role: str

    @field_validator("role", mode="after")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("student", "admin"):
            raise ValueError("role must be student or admin")
        return v


class UserStatusUpdate(BaseModel):
    is_active: bool


class PaginatedUsers(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    page_size: int


class UserCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user: UserOut
    temporary_password: Optional[str] = None
