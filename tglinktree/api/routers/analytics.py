"""Analytics endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from tglinktree.api.deps import get_db, rate_limit_auth, rate_limit_public
from tglinktree.api.auth import get_current_user
from tglinktree.models.user import User
from tglinktree.services import analytics_service

router = APIRouter(tags=["analytics"])


class TrackEventRequest(BaseModel):
    """Request body for fire-and-forget event tracking."""
    profile_id: int
    event_type: str  # 'profile_view', 'link_click', 'unlock_attempt', 'unlock_success'
    link_id: Optional[int] = None
    referrer: Optional[str] = None


@router.post("/track", status_code=202)
async def track_event(
    data: TrackEventRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _rate: None = Depends(rate_limit_public),
):
    """Fire-and-forget event tracking. No auth required, rate limited by IP."""
    client_ip = request.client.host if request.client else None

    await analytics_service.track_event(
        db=db,
        profile_id=data.profile_id,
        event_type=data.event_type,
        link_id=data.link_id,
        referrer=data.referrer,
        client_ip=client_ip,
    )
    return {"status": "accepted"}


@router.get("/profiles/me/analytics")
async def get_my_analytics(
    period: str = Query(default="7d", pattern=r"^\d+d$"),
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics for the authenticated user's profile."""
    return await analytics_service.get_analytics(db, user, period)
