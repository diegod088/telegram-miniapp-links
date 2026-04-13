"""Lock endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from tglinktree.api.deps import get_db, rate_limit_auth, rate_limit_lock_verify
from tglinktree.models.user import User
from tglinktree.schemas.lock import LockCreate, LockResponse, LockVerifyResponse
from tglinktree.services import lock_service

router = APIRouter(prefix="/locks", tags=["locks"])


@router.post("", response_model=LockResponse, status_code=201)
async def create_lock(
    data: LockCreate,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Create a lock on a link or profile (auth required, must own resource)."""
    lock = await lock_service.create_lock(db, user, data)
    return lock


@router.post("/{lock_id}/verify", response_model=LockVerifyResponse)
async def verify_lock(
    lock_id: int,
    user: User = Depends(rate_limit_lock_verify),
    db: AsyncSession = Depends(get_db),
):
    """Verify a lock as a visitor (rate limited: 10 req/60s)."""
    result = await lock_service.verify_lock(db, user, lock_id)
    return result


@router.delete("/{lock_id}", status_code=204)
async def delete_lock(
    lock_id: int,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Remove a lock (must own the profile)."""
    await lock_service.delete_lock(db, user, lock_id)
