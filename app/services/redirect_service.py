"""Redirect service — handling affiliate links and monetization logic."""

from __future__ import annotations

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import ProfileLink
from app.models.profile import Profile
from app.services import affiliate
from app.services.linkvertise import create_linkvertise_url
from app.repositories.link_repository import LinkRepository
from app.repositories.profile_repository import ProfileRepository
from app.core.exceptions import NotFoundError


class RedirectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.link_repo = LinkRepository(db)
        self.profile_repo = ProfileRepository(db)

    async def get_redirect_info(self, link_id: int, viewer_user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Prepare the final URL for a link click.
        Handles affiliate tagging and plan-based monetization (Linkvertise).
        """
        link = await self.link_repo.get(link_id)
        if not link:
            raise NotFoundError("Link not found")

        # 1. Get affiliate URL
        target_url = link.canonical_url or link.url
        affiliate_url = affiliate.get_affiliate_url(target_url)

        # 2. Determine viewer plan
        viewer_plan = "free"
        if viewer_user_id:
            viewer_profile = await self.profile_repo.get_by_user_id(viewer_user_id)
            if viewer_profile:
                viewer_plan = viewer_profile.plan

        # 3. Apply Linkvertise if free
        final_url = affiliate_url
        is_monetized = False
        
        if viewer_plan == "free":
            final_url = create_linkvertise_url(affiliate_url)
            is_monetized = True

        return {
            "url": final_url,
            "title": link.title,
            "is_monetized": is_monetized,
            "link_id": link.id,
            "profile_id": link.profile_id
        }
