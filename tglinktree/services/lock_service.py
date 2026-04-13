"""Lock service — create, verify, and manage content locks."""

from __future__ import annotations

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tglinktree.core.exceptions import (
    ForbiddenError,
    LockVerificationError,
    NotFoundError,
)
from tglinktree.models.link import ProfileLink
from tglinktree.models.lock import ContentLock, UserUnlock
from tglinktree.models.profile import Profile
from tglinktree.models.user import User
from tglinktree.schemas.lock import LockCreate, LockVerifyResponse
from tglinktree.services.telegram_service import check_channel_membership


# ── Plan-based lock type limits ───────────────────────────────
PLAN_LOCK_TYPES = {
    "free": {"channel_join"},
    "pro": {"channel_join", "payment", "password"},
    "business": {"channel_join", "payment", "password"},
}


async def create_lock(
    db: AsyncSession,
    user: User,
    data: LockCreate,
) -> ContentLock:
    """Create a content lock on a link or profile owned by the user."""
    # Resolve the profile
    if data.link_id is not None:
        result = await db.execute(
            select(ProfileLink)
            .join(Profile)
            .where(ProfileLink.id == data.link_id, Profile.user_id == user.id)
        )
        link = result.scalar_one_or_none()
        if link is None:
            raise NotFoundError("Link not found or you don't own it.")
        plan = link.profile.plan if hasattr(link, "profile") else "free"
        # Need to get profile for plan check
        profile_result = await db.execute(
            select(Profile).where(Profile.id == link.profile_id)
        )
        profile = profile_result.scalar_one()
        plan = profile.plan
    elif data.profile_id is not None:
        result = await db.execute(
            select(Profile).where(
                Profile.id == data.profile_id, Profile.user_id == user.id
            )
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            raise NotFoundError("Profile not found or you don't own it.")
        plan = profile.plan
    else:
        raise LockVerificationError("Must specify link_id or profile_id.")

    # Check lock type allowed for plan
    allowed_types = PLAN_LOCK_TYPES.get(plan, PLAN_LOCK_TYPES["free"])
    if data.lock_type not in allowed_types:
        raise ForbiddenError(
            f"Lock type '{data.lock_type}' is not available on the '{plan}' plan. "
            f"Allowed: {', '.join(allowed_types)}"
        )

    lock = ContentLock(
        link_id=data.link_id,
        profile_id=data.profile_id,
        lock_type=data.lock_type,
        config=data.config,
    )
    db.add(lock)
    await db.flush()
    return lock


async def verify_lock(
    db: AsyncSession,
    user: User,
    lock_id: int,
) -> LockVerifyResponse:
    """
    Verify a lock for a visitor.

    1. Check if already unlocked
    2. Dispatch to appropriate verifier based on lock_type
    3. On success: insert UserUnlock record
    """
    # Get the lock
    result = await db.execute(
        select(ContentLock).where(ContentLock.id == lock_id, ContentLock.is_active == True)
    )
    lock = result.scalar_one_or_none()
    if lock is None:
        raise NotFoundError("Lock not found or inactive.")

    # Check if already unlocked
    existing_unlock = await db.execute(
        select(UserUnlock).where(
            UserUnlock.lock_id == lock_id,
            UserUnlock.user_id == user.id,
        )
    )
    if existing_unlock.scalar_one_or_none():
        # Already unlocked — return the content URL
        url = await _get_locked_content_url(db, lock)
        return LockVerifyResponse(unlocked=True, url=url)

    # Dispatch by lock_type
    if lock.lock_type == "channel_join":
        return await _verify_channel_join(db, user, lock)
    elif lock.lock_type == "password":
        raise LockVerificationError("Password verification not implemented yet.")
    elif lock.lock_type == "payment":
        raise LockVerificationError("Payment verification not implemented yet.")
    else:
        raise LockVerificationError(f"Unknown lock type: {lock.lock_type}")


async def _verify_channel_join(
    db: AsyncSession,
    user: User,
    lock: ContentLock,
) -> LockVerifyResponse:
    """Verify channel_join lock type."""
    channel_id = lock.config.get("channel_id")
    if not channel_id:
        raise LockVerificationError("Lock misconfigured: missing channel_id.")

    try:
        is_member = await check_channel_membership(user.telegram_id, channel_id)
    except httpx.TimeoutException:
        raise LockVerificationError("Telegram API timeout. Try again later.")

    if not is_member:
        channel_name = lock.config.get("channel_name", channel_id)
        action_url = f"https://t.me/{channel_name.lstrip('@')}" if channel_name else None
        return LockVerifyResponse(
            unlocked=False,
            action_url=action_url,
            message=f"You must join the channel first.",
        )

    # Success — record unlock
    unlock = UserUnlock(
        lock_id=lock.id,
        user_id=user.id,
        method="channel_join",
    )
    db.add(unlock)
    await db.flush()

    url = await _get_locked_content_url(db, lock)
    return LockVerifyResponse(unlocked=True, url=url)


async def _get_locked_content_url(db: AsyncSession, lock: ContentLock) -> str | None:
    """Get the URL of the locked content."""
    if lock.link_id:
        result = await db.execute(
            select(ProfileLink).where(ProfileLink.id == lock.link_id)
        )
        link = result.scalar_one_or_none()
        return link.url if link else None
    return None


async def delete_lock(
    db: AsyncSession,
    user: User,
    lock_id: int,
) -> None:
    """Delete a lock (must own the profile)."""
    result = await db.execute(
        select(ContentLock).where(ContentLock.id == lock_id)
    )
    lock = result.scalar_one_or_none()
    if lock is None:
        raise NotFoundError("Lock not found.")

    # Verify ownership
    if lock.link_id:
        link_result = await db.execute(
            select(ProfileLink)
            .join(Profile)
            .where(ProfileLink.id == lock.link_id, Profile.user_id == user.id)
        )
        if link_result.scalar_one_or_none() is None:
            raise ForbiddenError("You don't own this lock.")
    elif lock.profile_id:
        profile_result = await db.execute(
            select(Profile).where(
                Profile.id == lock.profile_id, Profile.user_id == user.id
            )
        )
        if profile_result.scalar_one_or_none() is None:
            raise ForbiddenError("You don't own this lock.")

    await db.delete(lock)
    await db.flush()
