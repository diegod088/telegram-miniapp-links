"""Social router — endpoints for favorites and interactions."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.api.deps import get_db, rate_limit_auth
from app.models.user import User
from app.models.link import ProfileLink, LinkFavorite
from app.schemas.social import FavoriteToggleResponse, ActivityResponse
from app.api.auth import get_current_user
from app.services.activity_service import ActivityService

router = APIRouter(prefix="/social", tags=["social"], redirect_slashes=False)

@router.post("/links/{link_id}/favorite", response_model=FavoriteToggleResponse)
async def toggle_favorite(
    link_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Toggle a link as favorite for the current user.
    """
    # Check if link exists
    print(f"DEBUG: Toggling favorite for link {link_id} and user {user.id}")
    link = await db.get(ProfileLink, link_id)
    if not link:
        print(f"DEBUG: Link {link_id} not found")
        raise HTTPException(status_code=404, detail="Link not found")
        
    # Check if already favorited
    stmt = select(LinkFavorite).where(
        LinkFavorite.user_id == user.id,
        LinkFavorite.link_id == link_id
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    print(f"DEBUG: Existing favorite? {existing is not None}")
    
    activity_service = ActivityService(db)
    
    if existing:
        stmt = delete(LinkFavorite).where(
            LinkFavorite.user_id == user.id,
            LinkFavorite.link_id == link_id
        )
        await db.execute(stmt)
        await db.commit()
        return FavoriteToggleResponse(
            link_id=link_id,
            is_favorited=False,
            message="Eliminado de favoritos"
        )
    else:
        fav = LinkFavorite(user_id=user.id, link_id=link_id)
        db.add(fav)
        
        # Record activity
        # We use a flush here to ensure the favorite exists but wait for commit
        await activity_service.record_activity(
            type="new_favorite",
            message=f"{user.first_name or 'Alguien'} guardó el enlace '{link.title or 'VIP'}' como favorito",
            user_id=user.id,
            target_id=str(link_id),
            target_type="link"
        )
        
        await db.commit()
        return FavoriteToggleResponse(
            link_id=link_id,
            is_favorited=True,
            message="Añadido a favoritos"
        )

@router.get("/favorites")
async def get_my_favorites(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all links favorited by the current user.
    """
    from app.models.profile import Profile
    stmt = (
        select(ProfileLink, Profile)
        .join(LinkFavorite, LinkFavorite.link_id == ProfileLink.id)
        .join(Profile, ProfileLink.profile_id == Profile.id)
        .where(LinkFavorite.user_id == user.id)
        .order_by(LinkFavorite.created_at.desc())
    )
    print(f"DEBUG: Fetching favorites for user {user.id}")
    result = await db.execute(stmt)
    rows = result.all()
    print(f"DEBUG: Found {len(rows)} favorites")
    
    return [
        {
            "id": link.id,
            "title": link.title,
            "url": link.url,
            "category": link.category,
            "likes": link.likes,
            "clicks": link.clicks,
            "username": profile.slug,
            "display_name": profile.display_name
        }
        for link, profile in rows
    ]
