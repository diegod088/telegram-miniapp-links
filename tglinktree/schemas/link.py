"""Pydantic schemas for Link endpoints."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, field_validator


class LinkCreate(BaseModel):
    """Request body for adding a link."""
    url: str
    title: Optional[str] = None
    category: str = "OTHER"
    description: Optional[str] = None
    icon: Optional[str] = None
    link_type: str = "url"
    style: dict = {}

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v or len(v) > 256:
                raise ValueError("Title must be 1-256 characters.")
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("URL is required.")
        return v

    @field_validator("link_type")
    @classmethod
    def validate_link_type(cls, v: str) -> str:
        allowed = {"url", "telegram_channel", "telegram_bot", "payment"}
        if v not in allowed:
            raise ValueError(f"link_type must be one of: {', '.join(allowed)}")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        allowed = {"MOVIES", "SERIES", "ADULT", "VIP", "OTHER"}
        v = v.upper()
        if v not in allowed:
            return "OTHER"
        return v


class LinkUpdate(BaseModel):
    """Request body for editing a link."""
    title: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    is_premium: Optional[bool] = None
    category: Optional[str] = None
    link_type: Optional[str] = None
    style: Optional[dict] = None

    @field_validator("link_type")
    @classmethod
    def validate_link_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"url", "telegram_channel", "telegram_bot", "payment"}
            if v not in allowed:
                raise ValueError(f"link_type must be one of: {', '.join(allowed)}")
        return v


class LinkResponse(BaseModel):
    """Link response returned by the API."""
    id: int
    title: str
    url: str
    canonical_url: Optional[str] = None
    category: str
    description: Optional[str] = None
    icon: Optional[str] = None
    position: int
    is_active: bool
    is_verified: bool
    is_sponsored: bool
    upvotes: int
    views: int
    link_type: str
    style: dict = {}

    model_config = {"from_attributes": True}


class LinkReorder(BaseModel):
    """Request body for reordering links."""
    link_ids: list[int]

    @field_validator("link_ids")
    @classmethod
    def validate_link_ids(cls, v: list[int]) -> list[int]:
        if len(v) == 0:
            raise ValueError("link_ids must not be empty.")
        if len(v) != len(set(v)):
            raise ValueError("link_ids must not contain duplicates.")
        return v
