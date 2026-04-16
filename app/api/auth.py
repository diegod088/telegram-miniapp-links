"""Authentication dependency — extracts and verifies Telegram initData."""

from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.db.session import get_db
from app.core.exceptions import AuthenticationError, ForbiddenError
from app.core.security import verify_init_data
from app.models.user import User


async def get_current_user(
    x_init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that:
    1. Validates the X-Telegram-Init-Data header
    2. Upserts the user in the database
    3. Returns the User ORM object

    Raises:
        AuthenticationError: if initData is invalid or expired
        ForbiddenError: if the user is banned
    """
    settings = get_settings()

    # Verify init data
    data = verify_init_data(x_init_data, settings.BOT_TOKEN)
    tg_user = data["user"]

    telegram_id = tg_user.get("id")
    if not telegram_id:
        raise AuthenticationError("No user ID in initData")

    # Upsert user
    result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=tg_user.get("username"),
            first_name=tg_user.get("first_name"),
            photo_url=tg_user.get("photo_url"),
            lang_code=tg_user.get("language_code", "es"),
        )
        db.add(user)
        await db.flush()  # Get the ID without committing
    else:
        # Update fields that may have changed
        user.username = tg_user.get("username") or user.username
        user.first_name = tg_user.get("first_name") or user.first_name
        user.photo_url = tg_user.get("photo_url") or user.photo_url

    # Check ban
    if user.is_banned:
        raise ForbiddenError(f"User banned: {user.ban_reason or 'No reason given'}")

    # Inject 'plan' into the User object from their Profile (default to 'free')
    from app.models.profile import Profile
    plan_result = await db.execute(select(Profile.plan).where(Profile.user_id == user.id))
    user_plan = plan_result.scalar_one_or_none()
    setattr(user, "plan", user_plan or "free")

    return user


async def get_current_user_optional(
    x_init_data: str | None = Header(None, alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Optional version of get_current_user. Returns None if header missing/invalid."""
    if not x_init_data:
        return None
    try:
        return await get_current_user(x_init_data, db)
    except Exception:
        return None
