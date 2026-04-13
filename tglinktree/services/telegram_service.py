"""Telegram API service — channel membership checks with Redis caching."""

from __future__ import annotations

import json
import httpx

from tglinktree.config import get_settings
from tglinktree.core.redis import cache_get, cache_set


async def check_channel_membership(
    user_telegram_id: int,
    channel_id: str,
) -> bool:
    """
    Check if a Telegram user is a member of a channel/group.

    Uses Redis cache (300s TTL) before hitting the Telegram API.
    Timeout: 5 seconds. On timeout → raises httpx.TimeoutException
    (caller should handle and return HTTP 503).

    Returns:
        True if user is member/admin/creator, False otherwise.
    """
    # 1. Check Redis cache first
    cache_key = f"membership:{channel_id}:{user_telegram_id}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached == "1"

    # 2. Call Telegram API
    settings = get_settings()
    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/getChatMember"

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            url,
            params={
                "chat_id": channel_id,
                "user_id": user_telegram_id,
            },
        )

    if response.status_code != 200:
        # API error — don't cache, don't silently unlock
        await cache_set(cache_key, "0", ttl=60)  # Short cache for errors
        return False

    data = response.json()
    if not data.get("ok"):
        await cache_set(cache_key, "0", ttl=60)
        return False

    status = data.get("result", {}).get("status", "")
    is_member = status in ("member", "administrator", "creator")

    # 3. Cache result (300s)
    await cache_set(cache_key, "1" if is_member else "0", ttl=300)

    return is_member
