import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import LabeledPrice

from tglinktree.api.deps import get_db, rate_limit_auth
from tglinktree.config import get_settings
from tglinktree.models.payment import PendingInvoice
from tglinktree.models.user import User

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/create-invoice")
async def create_invoice(
    request: Request,
    plan_id: str,
    user: User = Depends(rate_limit_auth),
    db: AsyncSession = Depends(get_db),
):
    """Generate a Telegram Stars invoice link for a plan upgrade."""
    if plan_id not in ["pro", "business"]:
        raise HTTPException(status_code=400, detail="Plan inválido")

    # 1. Define prices in Stars (XTR)
    prices = {
        "pro": 100,      # 100 Stars
        "business": 300  # 300 Stars
    }
    amount = prices[plan_id]
    
    # 2. Generate unique payload for tracking
    invoice_payload = f"upgrade:{user.id}:{plan_id}:{uuid.uuid4().hex[:8]}"
    
    # 3. Create invoice link using the bot
    bot = request.app.state.bot
    try:
        invoice_link = await bot.create_invoice_link(
            title=f"Plan {plan_id.upper()} - TGLinktree",
            description=f"Suscripción de 30 días al plan {plan_id.upper()}",
            payload=invoice_payload,
            currency="XTR",
            prices=[LabeledPrice(label=f"Plan {plan_id.upper()}", amount=amount)],
        )
    except Exception as e:
        import logging
        logging.error(f"Error creating invoice: {e}")
        raise HTTPException(status_code=500, detail="Error al generar factura de Telegram")

    # 4. Save pending invoice
    pending = PendingInvoice(
        user_id=user.id,
        plan_id=plan_id,
        invoice_payload=invoice_payload,
        status="pending"
    )
    db.add(pending)
    await db.flush()

    return {"invoice_link": invoice_link}


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
