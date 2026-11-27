"""
IdeaScope – Job schemas.
Owner: Member 2 (Sufiyaan Imran)
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    target_id: int
    status: str
    progress: int
    attempts: int
    error: str | None
    result: Any | None
    created_by: int | None
    created_at: str
    started_at: str | None
    finished_at: str | None
