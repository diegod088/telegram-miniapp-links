"""Shared FastAPI dependencies — re-exports and rate limiting."""

from __future__ import annotations

import hashlib
from typing import Optional

from fastapi import Depends, Header, Request

from app.api.auth import get_current_user
from app.db.session import get_db
from app.core.exceptions import RateLimitError
from app.core.redis import check_rate_limit
from app.models.user import User

# Re-exports for convenience
__all__ = ["get_db", "get_current_user"]


# ── Rate Limiting Dependencies ────────────────────────────────

async def rate_limit_public(request: Request) -> None:
    """100 requests / 60 seconds per IP for public endpoints."""
    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]
    allowed = await check_rate_limit(f"public:{ip_hash}", 100, 60)
    if not allowed:
        raise RateLimitError()


async def rate_limit_auth(user: User = Depends(get_current_user)) -> User:
    """20 requests / 60 seconds per telegram_id for auth endpoints."""
    allowed = await check_rate_limit(f"auth:{user.telegram_id}", 20, 60)
    if not allowed:
        raise RateLimitError()
    return user


async def rate_limit_lock_verify(user: User = Depends(get_current_user)) -> User:
    """10 requests / 60 seconds per telegram_id for lock verify."""
    allowed = await check_rate_limit(f"lockverify:{user.telegram_id}", 10, 60)
    if not allowed:
        raise RateLimitError()
    return user
