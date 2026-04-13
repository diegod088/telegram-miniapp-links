"""Payments endpoints (stub — disabled by default)."""

from __future__ import annotations

from fastapi import APIRouter

from tglinktree.config import get_settings

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/plans")
async def list_plans():
    """Return available plan information."""
    return {
        "plans": [
            {
                "name": "free",
                "display_name": "Free",
                "max_links": get_settings().MAX_LINKS_FREE,
                "analytics_days": 7,
                "lock_types": ["channel_join"],
                "price": 0,
            },
            {
                "name": "pro",
                "display_name": "Pro",
                "max_links": get_settings().MAX_LINKS_PRO,
                "analytics_days": 90,
                "lock_types": ["channel_join", "payment", "password"],
                "themes": 5,
                "price": 4.99,
                "currency": "USD",
            },
            {
                "name": "business",
                "display_name": "Business",
                "max_links": get_settings().MAX_LINKS_BUSINESS,
                "analytics_days": 365,
                "lock_types": ["channel_join", "payment", "password"],
                "custom_domain": True,
                "price": 14.99,
                "currency": "USD",
            },
        ],
        "payments_enabled": get_settings().PAYMENTS_ENABLED,
    }
