"""Lock endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, rate_limit_auth, rate_limit_lock_verify
from app.models.user import User
from app.schemas.lock import LockCreate, LockResponse, LockVerifyResponse
from app.services.lock_service import LockService

router = APIRouter(prefix="/locks", tags=["locks"])


@router.post("", response_model=LockResponse, status_code=201)
async def create_lock(
    data: LockCreate,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Create a lock on a link or profile."""
    service = LockService(db)
    return await service.create_lock(user, data)


@router.post("/{lock_id}/verify", response_model=LockVerifyResponse)
async def verify_lock(
    lock_id: int,
    user: User = Depends(rate_limit_lock_verify),
    db: AsyncSession = Depends(get_db),
):
    """Verify a lock as a visitor."""
    service = LockService(db)
    return await service.verify_lock(user, lock_id)


@router.delete("/{lock_id}", status_code=204)
async def delete_lock(
    lock_id: int,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Remove a lock."""
    service = LockService(db)
    await service.delete_lock(user, lock_id)
