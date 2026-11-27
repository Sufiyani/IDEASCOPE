"""
IdeaScope – Job schemas.
Owner: Member 2 (Sufiyaan Imran)
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    target_id: int
    status: str
    progress: int
    attempts: int
    error: Optional[str]
    result: Optional[Any]
    created_by: Optional[int]
    created_at: str
    started_at: Optional[str]
    finished_at: Optional[str]
