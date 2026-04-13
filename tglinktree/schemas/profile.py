"""Pydantic schemas for Profile endpoints."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

RESERVED_SLUGS = frozenset({
    "api", "app", "admin", "www", "static", "me",
    "help", "bot", "support", "login",
})

SLUG_PATTERN = re.compile(r"^[a-z0-9_-]{3,64}$")


class ProfileCreate(BaseModel):
    """Request body for creating a profile."""
    slug: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    theme: str = "default"
    is_public: bool = True

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.lower().strip()
        if not SLUG_PATTERN.match(v):
            raise ValueError(
                "Slug must be 3-64 characters, lowercase letters, numbers, "
                "hyphens, or underscores only."
            )
        if v in RESERVED_SLUGS:
            raise ValueError(f"The slug '{v}' is reserved and cannot be used.")
        return v

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 128:
            raise ValueError("Display name must be 1-128 characters.")
        return v


class ProfileUpdate(BaseModel):
    """Request body for updating a profile."""
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    theme: Optional[str] = None
    is_public: Optional[bool] = None

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v or len(v) > 128:
                raise ValueError("Display name must be 1-128 characters.")
        return v


class LinkInProfile(BaseModel):
    """Nested link representation in profile responses."""
    id: int
    title: str
    url: str
    description: Optional[str] = None
    icon: Optional[str] = None
    position: int
    is_active: bool
    link_type: str
    style: dict = {}
    is_locked: bool = False
    lock_id: Optional[int] = None
    lock_type: Optional[str] = None

    model_config = {"from_attributes": True}


class ProfileResponse(BaseModel):
    """Full profile response returned by the API."""
    id: int
    slug: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    theme: str
    is_public: bool
    plan: str
    total_views: int
    created_at: datetime
    links: list[LinkInProfile] = []

    model_config = {"from_attributes": True}


class ProfilePublicResponse(BaseModel):
    """Public profile view — limited fields, includes lock status per link."""
    slug: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    theme: str
    total_views: int
    links: list[LinkInProfile] = []

    model_config = {"from_attributes": True}


class ExploreProfileItem(BaseModel):
    """Profile card for explore/discover view."""
    slug: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    plan: str
    link_count: int
    total_views: int

    model_config = {"from_attributes": True}


class ExploreResponse(BaseModel):
    """Response for GET /api/explore."""
    profiles: list[ExploreProfileItem]
    total: int
    has_more: bool
