"""Link service — business logic for profile links."""

from __future__ import annotations

import re
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import ProfileLink
from app.models.profile import Profile
from app.models.user import User
from app.schemas.link import LinkCreate, LinkUpdate
from app.repositories.link_repository import LinkRepository
from app.repositories.profile_repository import ProfileRepository
from app.services.social_service import SocialService
from app.services.discovery_service import DiscoveryService
from app.core.security import sanitize_text, validate_url
from app.core.exceptions import NotFoundError, ForbiddenError, ValidationError

logger = logging.getLogger("app")


class LinkService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.link_repo = LinkRepository(db)
        self.profile_repo = ProfileRepository(db)
        self.social_service = SocialService(db)
        self.discovery_service = DiscoveryService(db)


    async def get_own_link(self, user: User, link_id: int) -> ProfileLink:
        """Get a link that belongs to the user, or raise 404/403."""
        # Using a specialized query or checking ownership manually
        link = await self.link_repo.get(link_id)
        if not link:
            raise NotFoundError("Link not found.")
            
        profile = await self.profile_repo.get(link.profile_id)
        if not profile or profile.user_id != user.id:
            raise ForbiddenError("You don't own this link.")
            
        return link

    async def create_link(self, user: User, data: LinkCreate) -> ProfileLink:
        """Add a link to the user's profile."""
        from app.services.profile_service import ProfileService
        profile_service = ProfileService(self.db)
        
        # 1. Check daily limit
        await profile_service.check_daily_limit(user)
        
        # 1.1 Anti-spam cooldown (10 seconds)
        if user.last_link_created_at:
            time_since_last = datetime.utcnow() - user.last_link_created_at
            if time_since_last.total_seconds() < 10:
                raise ForbiddenError("Please wait a few seconds before adding another link.")

        profile = await profile_service.get_my_profile(user)
        
        # 2. Check total link limit
        await profile_service.check_link_total_limit(profile)

        # 2.1 Validate URL strictly
        if not validate_url(data.url):
            raise ValidationError("Invalid URL. Must be a well-formed http/https link.")

        # 3. Scrub URL
        canonical_url = await self.social_service.scrub_url(data.url)
        
        # 4. Scrape title if missing
        title = data.title
        if not title:
            scraped_title = await self.social_service.scrape_page_title(canonical_url)
            title = scraped_title or canonical_url

        # 5. Sanitize
        title = sanitize_text(title)
        link_description = sanitize_text(data.description)

        # 6. Determine next position
        existing_links = await self.link_repo.get_by_profile_id(profile.id)
        next_position = (existing_links[-1].position + 1) if existing_links else 0

        link_data = data.model_dump()
        link_data.update({
            "profile_id": profile.id,
            "title": title,
            "description": link_description,
            "canonical_url": canonical_url,
            "position": next_position,
        })
        
        link = await self.link_repo.create(**link_data)
        
        # 7. Update user statistics
        user.daily_link_count += 1
        user.last_link_created_at = datetime.utcnow()
        
        await self.db.flush()
        
        # 8. Update search index
        await self.discovery_service.update_search_vector(profile.id)
        
        return link

    async def update_link(self, user: User, link_id: int, data: LinkUpdate) -> ProfileLink:
        """Update a link owned by the user."""
        link = await self.get_own_link(user, link_id)
        
        update_data = data.model_dump(exclude_unset=True)
        
        if "title" in update_data:
            update_data["title"] = sanitize_text(update_data["title"])
        
        if "description" in update_data:
            update_data["description"] = sanitize_text(update_data["description"])
            
        if "url" in update_data:
            if not validate_url(update_data["url"]):
                raise ValidationError("Invalid URL.")
            update_data["canonical_url"] = await self.social_service.scrub_url(update_data["url"])

        # is_premium only editable by VIP users
        if "is_premium" in update_data:
            from app.services.profile_service import ProfileService
            profile = await ProfileService(self.db).get_my_profile(user)
            if profile.plan not in ("pro", "business"):
                update_data.pop("is_premium")

        updated_link = await self.link_repo.update(link.id, **update_data)
        await self.db.flush()
        
        # Update search index
        await self.discovery_service.update_search_vector(link.profile_id)
        return updated_link

    async def delete_link(self, user: User, link_id: int) -> None:
        """Delete a link owned by the user."""
        link = await self.get_own_link(user, link_id)
        profile_id = link.profile_id
        
        await self.link_repo.delete(link.id)
        await self.db.flush()
        
        # Update search index
        await self.discovery_service.update_search_vector(profile_id)

    async def reorder_links(self, user: User, link_ids: List[int]) -> None:
        """Reorder links for the user's profile."""
        from app.services.profile_service import ProfileService
        profile = await ProfileService(self.db).get_my_profile(user)

        # Get all links for this profile
        existing_links = await self.link_repo.get_by_profile_id(profile.id)
        links_dict = {l.id: l for l in existing_links}

        # Validate and update positions
        for i, lid in enumerate(link_ids):
            if lid not in links_dict:
                raise NotFoundError(f"Link {lid} not found in your profile.")
            links_dict[lid].position = i

        await self.db.flush()

    async def boost_link(self, user: User, link_id: int) -> ProfileLink:
        """Boost a link for 24h."""
        from app.services.profile_service import ProfileService
        profile = await ProfileService(self.db).get_my_profile(user)
        
        if profile.plan not in ["pro", "business"]:
            raise ForbiddenError("Upgrade help reach more people with Boost.")

        link = await self.get_own_link(user, link_id)
        boosted_until = datetime.utcnow() + timedelta(days=1)
        
        return await self.link_repo.update(link.id, boosted_until=boosted_until)
