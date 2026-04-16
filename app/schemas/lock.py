"""Pydantic schemas for Lock endpoints."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, field_validator, model_validator


class LockCreate(BaseModel):
    """Request body for creating a content lock."""
    link_id: Optional[int] = None
    profile_id: Optional[int] = None
    lock_type: str
    config: dict

    @field_validator("lock_type")
    @classmethod
    def validate_lock_type(cls, v: str) -> str:
        allowed = {"channel_join", "payment", "password"}
        if v not in allowed:
            raise ValueError(f"lock_type must be one of: {', '.join(allowed)}")
        return v

    @model_validator(mode="after")
    def exactly_one_target(self) -> "LockCreate":
        if (self.link_id is None) == (self.profile_id is None):
            raise ValueError(
                "Exactly one of link_id or profile_id must be provided."
            )
        return self


class LockResponse(BaseModel):
    """Lock response returned by the API."""
    id: int
    link_id: Optional[int] = None
    profile_id: Optional[int] = None
    lock_type: str
    config: dict
    is_active: bool

    model_config = {"from_attributes": True}


class LockVerifyResponse(BaseModel):
    """Response from lock verification."""
    unlocked: bool
    url: Optional[str] = None
    action_url: Optional[str] = None
    message: Optional[str] = None
