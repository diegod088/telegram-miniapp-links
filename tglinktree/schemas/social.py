"""Social schemas — feed and upvotes."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

class UserMinimal(BaseModel):
    """Minimal user info for feed items."""
    username: Optional[str] = None
    first_name: Optional[str] = None

    model_config = {"from_attributes": True}

class ExploreFeedItem(BaseModel):
    """A link item in the social explore feed."""
    id: int
    title: str
    url: str
    canonical_url: Optional[str] = None
    category: str
    upvotes: int
    views: int
    created_at: datetime
    is_sponsored: bool
    is_verified: bool
    
    # Nested user info (from Profile's user)
    username: Optional[str] = None
    first_name: Optional[str] = None

    model_config = {"from_attributes": True}

class ExploreFeedResponse(BaseModel):
    """Response for GET /api/explore/feed."""
    items: List[ExploreFeedItem]
    next_cursor: Optional[str] = None # ISO timestamp of the last item's created_at

class UpvoteResponse(BaseModel):
    """Response for POST /api/links/{id}/upvote."""
    upvotes: int
    is_upvoted: bool
