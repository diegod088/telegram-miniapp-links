"""Middleware/Dependencies for enforcing plan-based limits."""

from fastapi import Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tglinktree.api.deps import get_db, get_current_user
from tglinktree.config import get_settings
from tglinktree.models.link import ProfileLink
from tglinktree.models.profile import Profile
from tglinktree.models.user import User

async def check_link_limit(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Dependency to check if the user has reached their link limit.
    Raises 403 Forbidden if the limit is reached.
    """
    # 1. Get user's profile
    stmt = select(Profile).where(Profile.user_id == user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    
    if not profile:
        # Should not happen if endpoints are used correctly after profile creation
        return

    # 2. Count existing links
    count_stmt = select(func.count()).select_from(ProfileLink).where(ProfileLink.profile_id == profile.id)
    count_result = await db.execute(count_stmt)
    current_count = count_result.scalar() or 0
    
    # 3. Determine limit
    settings = get_settings()
    plan_limits = {
        "free": settings.MAX_LINKS_FREE,
        "pro": settings.MAX_LINKS_PRO,
        "business": settings.MAX_LINKS_BUSINESS,
    }
    
    limit = plan_limits.get(profile.plan.lower(), settings.MAX_LINKS_FREE)
    
    if current_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Has alcanzado el límite de {limit} links para tu plan {profile.plan.upper()}. "
                   "Actualiza tu cuenta para añadir más."
        )
