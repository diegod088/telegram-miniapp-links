"""Profile service — business logic for profiles."""

from __future__ import annotations

from datetime import date
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.core.exceptions import ForbiddenError, NotFoundError, PlanLimitError
from app.models.profile import Profile
from app.models.user import User
from app.schemas.profile import ProfileCreate, ProfileUpdate
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.core.security import sanitize_text, validate_slug, is_slug_reserved
from app.core.exceptions import ValidationError


class ProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repo = ProfileRepository(db)
        self.user_repo = UserRepository(db)

    def _get_max_links(self, plan: str) -> int:
        settings = get_settings()
        return {
            "free": settings.MAX_LINKS_FREE,
            "pro": settings.MAX_LINKS_PRO,
            "business": settings.MAX_LINKS_BUSINESS,
        }.get(plan, settings.MAX_LINKS_FREE)

    def get_boost_score(self, plan: str) -> float:
        return {
            "free": 1.0,
            "pro": 1.2,
            "business": 1.5,
        }.get(plan.lower(), 1.0)

    async def create_profile(self, user: User, data: ProfileCreate) -> Profile:
        """Create a new profile for the user."""
        # Check user doesn't already have a profile
        existing = await self.profile_repo.get_by_user_id(user.id)
        if existing:
            raise ForbiddenError("You already have a profile. Use PATCH to update it.")
            
        # 0. Validate slug format and reservation
        if not validate_slug(data.slug):
            raise ValidationError("Slug must be 3-32 alphanumeric characters.")
        if is_slug_reserved(data.slug):
            raise ForbiddenError(f"The slug '{data.slug}' is reserved.")

        # Check slug uniqueness
        existing_by_slug = await self.profile_repo.get_by_slug(data.slug)
        if existing_by_slug:
            # Self-healing logic if Telegram ID matches
            # This logic might be moved to a higher-level orchestration if needed
            # For now, keeping it here but using repo
            if existing_by_slug.user_id != user.id:
                # We need to check if the other user has the same telegram_id
                # This requires fetching the other user
                other_user = await self.user_repo.get(existing_by_slug.user_id)
                if other_user and other_user.telegram_id == user.telegram_id:
                    existing_by_slug.user_id = user.id
                    await self.db.flush()
                    return await self.profile_repo.get_by_user_id(user.id, include_links=True)
                
                raise ForbiddenError(f"The slug '{data.slug}' is already taken.")

        plan = data.plan if hasattr(data, 'plan') else "free"
        profile_data = data.model_dump()
        
        # 3. Sanitize inputs
        profile_data["display_name"] = sanitize_text(profile_data.get("display_name"))
        profile_data["bio"] = sanitize_text(profile_data.get("bio"))

        if 'plan' not in profile_data:
            profile_data['plan'] = plan
            
        profile_data['user_id'] = user.id
        profile_data['boost_score'] = self.get_boost_score(plan)
        
        return await self.profile_repo.create(**profile_data)

    async def get_my_profile(self, user: User) -> Profile:
        """Get the profile owned by the given user."""
        profile = await self.profile_repo.get_by_user_id(user.id, include_links=True)
        if not profile:
            raise NotFoundError("You don't have a profile yet. Create one first.")
        return profile

    async def get_public_profile(self, slug: str) -> Profile:
        """Get a public profile by slug."""
        profile = await self.profile_repo.get_by_slug(slug, include_links=True)
        if not profile or not profile.is_public:
            raise NotFoundError(f"Profile '{slug}' not found.")

        # Increment view count
        profile.total_views += 1
        await self.db.flush()
        return profile

    async def update_profile(self, user: User, data: ProfileUpdate) -> Profile:
        """Update the user's profile."""
        profile = await self.get_my_profile(user)
        
        update_data = data.model_dump(exclude_unset=True)
        if "plan" in update_data:
            update_data["boost_score"] = self.get_boost_score(update_data["plan"])
            
        if "display_name" in update_data:
            update_data["display_name"] = sanitize_text(update_data["display_name"])
        if "bio" in update_data:
            update_data["bio"] = sanitize_text(update_data["bio"])

        updated_profile = await self.profile_repo.update(profile.id, **update_data)
        
        # Update search index (Discovery Service)
        from app.services.discovery_service import DiscoveryService
        discovery = DiscoveryService(self.db)
        await discovery.update_search_vector(profile.id)

        return updated_profile

    async def check_daily_limit(self, user: User) -> None:
        """Check daily link creation limit for free users."""
        today = date.today()
        if user.last_reset_date is None or today > user.last_reset_date:
            user.daily_link_count = 0
            user.last_reset_date = today
            await self.db.flush()

        profile = await self.profile_repo.get_by_user_id(user.id)
        plan = profile.plan if profile else "free"

        if plan == "free" and user.daily_link_count >= 3:
            raise PlanLimitError(
                message="Límite diario alcanzado. Hazte VIP para links ilimitados.",
                current_plan="free"
            )

    async def check_link_total_limit(self, profile: Profile) -> None:
        """Check total link limit for the profile's plan."""
        # This will be refined once we have a fully implemented link repo method for counting
        from app.models.link import ProfileLink
        from sqlalchemy import select
        stmt = select(func.count()).select_from(ProfileLink).where(ProfileLink.profile_id == profile.id)
        res = await self.db.execute(stmt)
        current_count = res.scalar() or 0
        
        max_allowed = self._get_max_links(profile.plan)
        if current_count >= max_allowed:
            raise PlanLimitError(
                message=f"You've reached the maximum of {max_allowed} links on your '{profile.plan}' plan.",
                current_plan=profile.plan,
            )
