"""Handlers for Telegram Stars payments."""

import logging
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes, PreCheckoutQueryHandler, MessageHandler, filters
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from tglinktree.core.database import async_session_factory
from tglinktree.models.payment import PendingInvoice, Subscription
from tglinktree.models.profile import Profile
from tglinktree.models.user import User
from tglinktree.services.profile_service import _boost_score_for_plan

logger = logging.getLogger("tglinktree.bot.payments")

async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answer the pre-checkout query to allow the payment to proceed."""
    query = update.pre_checkout_query
    # We could verify the payload here if needed, but for now we'll just allow it
    await query.answer(ok=True)

async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle a successful payment and upgrade the user's plan."""
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    
    logger.info(f"Successful payment received: {payload}")
    
    async with async_session_factory() as db:
        # 1. Find the pending invoice
        stmt = select(PendingInvoice).where(PendingInvoice.invoice_payload == payload)
        result = await db.execute(stmt)
        pending = result.scalar_one_or_none()
        
        if not pending or pending.status != "pending":
            logger.warning(f"Received payment for unknown or processed payload: {payload}")
            return

        # 2. Get user and profile
        user_stmt = select(User).where(User.id == pending.user_id)
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        
        profile_stmt = select(Profile).where(Profile.user_id == pending.user_id)
        profile_res = await db.execute(profile_stmt)
        profile = profile_res.scalar_one_or_none()
        
        if not profile:
            logger.error(f"User {pending.user_id} paid but has no profile!")
            return

        # 3. Upgrade Plan and Boost
        plan_id = pending.plan_id
        profile.plan = plan_id
        profile.boost_score = _boost_score_for_plan(plan_id)
        
        # 4. Create/Update Subscription record
        expires_at = datetime.utcnow() + timedelta(days=30)
        new_sub = Subscription(
            user_id=user.id,
            plan=plan_id,
            status="active",
            provider="telegram_stars",
            amount=payment.total_amount,
            currency=payment.currency,
            started_at=datetime.utcnow(),
            expires_at=expires_at
        )
        db.add(new_sub)
        
        # 5. Mark invoice as completed
        pending.status = "completed"
        
        await db.commit()
        
        # 6. Notify the user
        await update.message.reply_text(
            f"🎉 **¡Pago recibido!**\n\n"
            f"Tu cuenta ha sido mejorada al plan **{plan_id.upper()}**.\n"
            f"Ahora tienes acceso a más links y mayor visibilidad en el feed.\n\n"
            f"La suscripción expira el: {expires_at.strftime('%Y-%m-%d')}",
            parse_mode="Markdown"
        )

def get_payment_handlers():
    """Return the list of handlers for registration."""
    return [
        PreCheckoutQueryHandler(pre_checkout_handler),
        MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler),
    ]
