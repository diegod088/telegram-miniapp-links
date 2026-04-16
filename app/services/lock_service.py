"""Lock service — create, verify, and manage content locks."""

from __future__ import annotations

from typing import Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import ForbiddenError, LockVerificationError, NotFoundError
from app.models.link import ProfileLink
from app.models.lock import ContentLock, UserUnlock
from app.models.profile import Profile
from app.models.user import User
from app.schemas.lock import LockCreate, LockVerifyResponse
from app.services.telegram_service import check_channel_membership
from app.repositories.link_repository import LinkRepository
from app.repositories.profile_repository import ProfileRepository

PLAN_LOCK_TYPES = {
    "free": {"channel_join"},
    "pro": {"channel_join", "payment", "password"},
    "business": {"channel_join", "payment", "password"},
}


class LockService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.link_repo = LinkRepository(db)
        self.profile_repo = ProfileRepository(db)

    async def create_lock(self, user: User, data: LockCreate) -> ContentLock:
        """Create a content lock on a link or profile owned by the user."""
        profile = None
        plan = "free"
        
        if data.link_id is not None:
            link = await self.link_repo.get(data.link_id)
            if not link:
                raise NotFoundError("Link not found.")
            
            profile = await self.profile_repo.get(link.profile_id)
            if not profile or profile.user_id != user.id:
                raise ForbiddenError("You don't own this link.")
            plan = profile.plan
        elif data.profile_id is not None:
            profile = await self.profile_repo.get(data.profile_id)
            if not profile or profile.user_id != user.id:
                raise ForbiddenError("You don't own this profile.")
            plan = profile.plan
        else:
            raise LockVerificationError("Must specify link_id or profile_id.")

        # Check lock type allowed for plan
        allowed_types = PLAN_LOCK_TYPES.get(plan, PLAN_LOCK_TYPES["free"])
        if data.lock_type not in allowed_types:
            raise ForbiddenError(
                f"Lock type '{data.lock_type}' is not available on your plan."
            )

        lock = ContentLock(
            link_id=data.link_id,
            profile_id=data.profile_id,
            lock_type=data.lock_type,
            config=data.config,
        )
        self.db.add(lock)
        await self.db.flush()
        return lock

    async def verify_lock(self, user: User, lock_id: int) -> LockVerifyResponse:
        """Verify a lock for a visitor."""
        stmt = select(ContentLock).where(ContentLock.id == lock_id, ContentLock.is_active == True)
        res = await self.db.execute(stmt)
        lock = res.scalar_one_or_none()
        if not lock:
            raise NotFoundError("Lock not found or inactive.")

        # Check if already unlocked
        stmt_unlock = select(UserUnlock).where(
            UserUnlock.lock_id == lock_id,
            UserUnlock.user_id == user.id
        )
        res_unlock = await self.db.execute(stmt_unlock)
        if res_unlock.scalar_one_or_none():
            url = await self._get_locked_content_url(lock)
            return LockVerifyResponse(unlocked=True, url=url)

        # Verification logic based on type
        if lock.lock_type == "channel_join":
            return await self._verify_channel_join(user, lock)
        # More types can be added here
        else:
            raise LockVerificationError(f"Verification for {lock.lock_type} not yet implemented.")

    async def _verify_channel_join(self, user: User, lock: ContentLock) -> LockVerifyResponse:
        channel_id = lock.config.get("channel_id")
        if not channel_id:
            raise LockVerificationError("Lock misconfigured: missing channel_id.")

        is_member = await check_channel_membership(user.telegram_id, channel_id)
        if not is_member:
            channel_name = lock.config.get("channel_name", channel_id)
            return LockVerifyResponse(
                unlocked=False,
                action_url=f"https://t.me/{channel_name.lstrip('@')}" if channel_name else None,
                message="Deberás unirte al canal primero."
            )

        # Success - record unlock
        unlock = UserUnlock(lock_id=lock.id, user_id=user.id, method="channel_join")
        self.db.add(unlock)
        await self.db.flush()

        url = await self._get_locked_content_url(lock)
        return LockVerifyResponse(unlocked=True, url=url)

    async def _get_locked_content_url(self, lock: ContentLock) -> Optional[str]:
        if lock.link_id:
            link = await self.link_repo.get(lock.link_id)
            return link.url if link else None
        return None

    async def delete_lock(self, user: User, lock_id: int) -> None:
        """Delete a lock."""
        res = await self.db.execute(select(ContentLock).where(ContentLock.id == lock_id))
        lock = res.scalar_one_or_none()
        if not lock:
            raise NotFoundError("Lock not found.")

        # Ownership check
        if lock.link_id:
            link = await self.link_repo.get(lock.link_id)
            profile = await self.profile_repo.get(link.profile_id)
            if not profile or profile.user_id != user.id:
                raise ForbiddenError("Ownership verification failed.")
        elif lock.profile_id:
            profile = await self.profile_repo.get(lock.profile_id)
            if not profile or profile.user_id != user.id:
                raise ForbiddenError("Ownership verification failed.")

        await self.db.delete(lock)
        await self.db.flush()
