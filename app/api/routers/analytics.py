"""Analytics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, rate_limit_auth
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=dict)
async def get_my_analytics(
    period: str = Query("7d", regex="^(7d|30d|90d|365d)$"),
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated statistics for the user's profile.
    Available periods: 7d, 30d, 90d, 365d.
    Plan limits apply (Free: 7d, Pro: 90d, Business: 365d).
    """
    service = AnalyticsService(db)
    return await service.get_stats(user, period)
