"""Profile service — business logic for profiles."""

from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import select, func
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


async def check_daily_limit(db: AsyncSession, user: User) -> None:
    """
    Check if a free user has reached their daily link creation limit.
    Free limit: 3 links per 24h.
    """
    # 1. Handle Reset
    today = date.today()
    if user.last_reset_date is None or today > user.last_reset_date:
        user.daily_link_count = 0
        user.last_reset_date = today
        await db.flush()

    # 2. Check Plan and Limit
    # We need the profile to check the current plan (profiles are linked to users)
    # However, the user said "Si plan='free'". 
    # Usually users have one profile. Let's fetch it.
    stmt = select(Profile.plan).where(Profile.user_id == user.id)
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none() or "free"

    if plan == "free" and user.daily_link_count >= 3:
        from tglinktree.core.exceptions import PlanLimitError
        raise PlanLimitError(
            message="Límite diario alcanzado. Hazte VIP para links ilimitados.",
            current_plan="free"
        )


def _boost_score_for_plan(plan: str) -> float:
    return {
        "free": 1.0,
        "pro": 1.2,
        "business": 1.5,
    }.get(plan.lower(), 1.0)


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
        select(Profile)
        .where(Profile.slug == data.slug)
        .options(selectinload(Profile.user))
    )
    existing_by_slug = slug_check.scalar_one_or_none()
    
    if existing_by_slug:
        # SELF-HEALING: If the slug belongs to the same Telegram ID, re-link it
        if existing_by_slug.user and existing_by_slug.user.telegram_id == user.telegram_id:
            print(f"Self-healing: Re-linking profile '{data.slug}' to user ID {user.id} (matching Telegram ID {user.telegram_id})")
            existing_by_slug.user_id = user.id
            await db.flush()
            
            # Eagerly load links and locks for the return response
            # We need to re-query or refresh because selectinload on an existing object can be tricky
            result = await db.execute(
                select(Profile)
                .where(Profile.id == existing_by_slug.id)
                .options(selectinload(Profile.links).selectinload(ProfileLink.locks))
            )
            return result.scalar_one()
            
        raise ForbiddenError(f"The slug '{data.slug}' is already taken.")

    profile = Profile(
        user_id=user.id,
        slug=data.slug,
        display_name=data.display_name,
        bio=data.bio,
        avatar_url=data.avatar_url,
        theme=data.theme,
        is_public=data.is_public,
        plan=data.plan if hasattr(data, 'plan') else "free",
        boost_score=_boost_score_for_plan(data.plan if hasattr(data, 'plan') else "free"),
        links=[]
    )
    db.add(profile)
    await db.flush()
    return profile


async def get_profile_by_user(db: AsyncSession, user: User) -> Profile:
    """Get the profile owned by the given user."""
    print(f"DEBUG: Searching profile for user_id={user.id} (tg={user.telegram_id})")
    result = await db.execute(
        select(Profile)
        .where(Profile.user_id == user.id)
        .options(selectinload(Profile.links).selectinload(ProfileLink.locks))
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        print(f"DEBUG: No profile found for user_id={user.id}")
        raise NotFoundError("You don't have a profile yet. Create one first.")
    
    print(f"DEBUG: Found profile id={profile.id} for user_id={user.id}")
    return profile


async def get_profile_by_slug(db: AsyncSession, slug: str) -> Profile:
    """Get a public profile by slug, with links eagerly loaded."""
    result = await db.execute(
        select(Profile)
        .where(Profile.slug == slug, Profile.is_public == True)
        .options(selectinload(Profile.links).selectinload(ProfileLink.locks))
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
        if field == "plan":
            profile.boost_score = _boost_score_for_plan(value)

    await db.flush()

    # Update search index since name/bio/category might have changed
    from tglinktree.services import discovery_service
    await discovery_service.update_search_vector(db, profile.id)

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
