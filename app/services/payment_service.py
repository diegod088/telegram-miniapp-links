"""Payment service — handling plans, invoices, and subscriptions."""

from __future__ import annotations

import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Bot, LabeledPrice

from app.core.settings import get_settings
from app.models.payment import PendingInvoice
from app.models.user import User
from app.core.exceptions import ForbiddenError


class PaymentService:
    def __init__(self, db: AsyncSession, bot: Optional[Bot] = None):
        self.db = db
        self.bot = bot

    async def create_plan_invoice(self, user: User, plan_id: str) -> str:
        """Generate a Telegram Stars invoice link for a plan upgrade."""
        if plan_id not in ["pro", "business"]:
            raise ValueError("Plan inválido")

        if not self.bot:
            raise RuntimeError("Bot instance required for creating invoices")

        # 1. Define prices in Stars (XTR)
        prices = {
            "pro": 100,      # 100 Stars
            "business": 300  # 300 Stars
        }
        amount = prices[plan_id]
        
        # 2. Generate unique payload
        invoice_payload = f"upgrade:{user.id}:{plan_id}:{uuid.uuid4().hex[:8]}"
        
        # 3. Create invoice link
        invoice_link = await self.bot.create_invoice_link(
            title=f"Plan {plan_id.upper()} - TGLinktree",
            description=f"Suscripción de 30 días al plan {plan_id.upper()}",
            payload=invoice_payload,
            currency="XTR",
            prices=[LabeledPrice(label=f"Plan {plan_id.upper()}", amount=amount)],
        )

        # 4. Save pending invoice
        pending = PendingInvoice(
            user_id=user.id,
            plan_id=plan_id,
            invoice_payload=invoice_payload,
            status="pending"
        )
        self.db.add(pending)
        await self.db.flush()

        return invoice_link

    def get_available_plans(self) -> Dict[str, Any]:
        """Return details of all available plans."""
        settings = get_settings()
        return {
            "plans": [
                {
                    "name": "free",
                    "display_name": "Free",
                    "max_links": settings.MAX_LINKS_FREE,
                    "analytics_days": 7,
                    "lock_types": ["channel_join"],
                    "price": 0,
                },
                {
                    "name": "pro",
                    "display_name": "Pro",
                    "max_links": settings.MAX_LINKS_PRO,
                    "analytics_days": 90,
                    "lock_types": ["channel_join", "payment", "password"],
                    "price": 100,
                    "currency": "XTR",
                },
                {
                    "name": "business",
                    "display_name": "Business",
                    "max_links": settings.MAX_LINKS_BUSINESS,
                    "analytics_days": 365,
                    "lock_types": ["channel_join", "payment", "password"],
                    "price": 300,
                    "currency": "XTR",
                },
            ],
            "payments_enabled": settings.PAYMENTS_ENABLED,
        }
