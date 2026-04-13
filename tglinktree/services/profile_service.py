"""Profile service — business logic for profiles."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tglinktree.config import get_settings
from tglinktree.core.exceptions import ForbiddenError, NotFoundError, PlanLimitError
from tglinktree.models.link import ProfileLink
from tglinktree.models.profile import Profile
from tglinktree.models.user import User
from tglinktree.schemas.profile import ProfileCreate, ProfileUpdate, RESERVED_SLUGS


# ── Plan link limits ──────────────────────────────────────────
def _max_links_for_plan(plan: str) -> int:
    settings = get_settings()
    return {
        "free": settings.MAX_LINKS_FREE,
        "pro": settings.MAX_LINKS_PRO,
        "business": settings.MAX_LINKS_BUSINESS,
    }.get(plan, settings.MAX_LINKS_FREE)


# ── CRUD ──────────────────────────────────────────────────────

async def create_profile(
    db: AsyncSession,
    user: User,
    data: ProfileCreate,
) -> Profile:
    """Create a new profile for the user."""
    # Check user doesn't already have a profile
    existing = await db.execute(
        select(Profile).where(Profile.user_id == user.id)
    )
    if existing.scalar_one_or_none():
        raise ForbiddenError("You already have a profile. Use PATCH to update it.")

    # Check slug uniqueness (also enforced by DB, but better error msg)
    slug_check = await db.execute(
        select(Profile).where(Profile.slug == data.slug)
    )
    if slug_check.scalar_one_or_none():
        raise ForbiddenError(f"The slug '{data.slug}' is already taken.")

    profile = Profile(
        user_id=user.id,
        slug=data.slug,
        display_name=data.display_name,
        bio=data.bio,
        avatar_url=data.avatar_url,
        theme=data.theme,
        is_public=data.is_public,
        links=[]
    )
    db.add(profile)
    await db.flush()
    return profile


async def get_profile_by_user(db: AsyncSession, user: User) -> Profile:
    """Get the profile owned by the given user."""
    result = await db.execute(
        select(Profile)
        .where(Profile.user_id == user.id)
        .options(selectinload(Profile.links))
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise NotFoundError("You don't have a profile yet. Create one first.")
    return profile


async def get_profile_by_slug(db: AsyncSession, slug: str) -> Profile:
    """Get a public profile by slug, with links eagerly loaded."""
    result = await db.execute(
        select(Profile)
        .where(Profile.slug == slug, Profile.is_public == True)
        .options(selectinload(Profile.links))
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise NotFoundError(f"Profile '{slug}' not found.")

    # Increment view count
    profile.total_views += 1

    return profile


async def update_profile(
    db: AsyncSession,
    user: User,
    data: ProfileUpdate,
) -> Profile:
    """Update the user's profile with the provided fields."""
    profile = await get_profile_by_user(db, user)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.flush()
    return profile


async def check_link_limit(db: AsyncSession, profile: Profile) -> None:
    """Raise PlanLimitError if the profile has reached its link limit."""
    result = await db.execute(
        select(ProfileLink).where(ProfileLink.profile_id == profile.id)
    )
    current_count = len(result.scalars().all())
    max_allowed = _max_links_for_plan(profile.plan)

    if current_count >= max_allowed:
        raise PlanLimitError(
            message=f"You've reached the maximum of {max_allowed} links on your "
                    f"'{profile.plan}' plan. Upgrade to add more.",
            current_plan=profile.plan,
        )
