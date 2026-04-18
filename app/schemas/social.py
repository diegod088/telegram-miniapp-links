"""Pydantic schemas for social features."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ActivityResponse(BaseModel):
    id: int
    user_id: Optional[int]
    type: str # 'profile_creation', 'link_trending', etc.
    message: str
    target_id: Optional[str]
    target_type: Optional[str]
    created_at: datetime
    
    # Optional nested user info for display
    username: Optional[str] = None
    first_name: Optional[str] = None

    class Config:
        from_attributes = True

class FavoriteToggleResponse(BaseModel):
    link_id: int
    is_favorited: bool
    message: str

class ExploreFeedItem(BaseModel):
    id: int
    title: str = "Sin título"
    url: str = "#"
    canonical_url: Optional[str] = None
    category: str = "OTHER"
    likes: int = 0
    dislikes: int = 0
    clicks: int = 0
    created_at: datetime = datetime.utcnow()
    is_sponsored: bool = False
    is_verified: bool = False
    is_featured: bool = False
    username: Optional[str] = "usuario"
    first_name: Optional[str] = None
    display_name: Optional[str] = None
    profile_slug: Optional[str] = None
    thumbnail_url: Optional[str] = None
    rank: Optional[int] = None

    class Config:
        from_attributes = True

class ExploreFeedResponse(BaseModel):
    items: List[ExploreFeedItem]
    next_cursor: Optional[str] = None

class SocialActionResponse(BaseModel):
    likes: int
    dislikes: int
    is_liked: Optional[bool] = None
    is_disliked: Optional[bool] = None

class FeedResponse(BaseModel):
    items: List[ExploreFeedItem]
    next_page: Optional[int] = None
    next_cursor: Optional[str] = None
    has_more: bool = False
