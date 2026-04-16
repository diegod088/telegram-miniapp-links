"""Handlers for Telegram Stars payments."""

import logging
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes, PreCheckoutQueryHandler, MessageHandler, filters

from app.db.session import async_session_factory
from app.models.payment import PendingInvoice, Subscription
from app.repositories.user_repository import UserRepository
from app.repositories.profile_repository import ProfileRepository
from app.services.profile_service import ProfileService

logger = logging.getLogger("app.bot.payments")


async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answer the pre-checkout query to allow the payment to proceed."""
    query = update.pre_checkout_query
    await query.answer(ok=True)


async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle a successful payment and upgrade the user's plan."""
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    
    logger.info(f"Successful payment received: {payload}")
    
    async with async_session_factory() as db:
        # 1. Use repositories/services for cleanup
        user_repo = UserRepository(db)
        profile_repo = ProfileRepository(db)
        profile_service = ProfileService(db)
        
        # 2. Find the pending invoice (direct query fine for specialized tracking or add a repo)
        from sqlalchemy import select
        stmt = select(PendingInvoice).where(PendingInvoice.invoice_payload == payload)
        result = await db.execute(stmt)
        pending = result.scalar_one_or_none()
        
        if not pending or pending.status != "pending":
            logger.warning(f"Duplicate or invalid payment payload: {payload}")
            return

        # 3. Fetch user and profile
        user = await user_repo.get(pending.user_id)
        profile = await profile_repo.get_by_user_id(pending.user_id)
        
        if not profile or not user:
            logger.error(f"User/Profile missing for payment {payload}")
            return

        # 4. Upgrade logic
        plan_id = pending.plan_id
        profile.plan = plan_id
        profile.boost_score = profile_service.get_boost_score(plan_id)
        
        # 5. Create Subscription
        expires_at = datetime.utcnow() + timedelta(days=30)
        subscription = Subscription(
            user_id=user.id,
            plan=plan_id,
            status="active",
            provider="telegram_stars",
            amount=payment.total_amount,
            currency=payment.currency,
            started_at=datetime.utcnow(),
            expires_at=expires_at
        )
        db.add(subscription)
        
        # 6. Mark invoice as completed
        pending.status = "completed"
        
        await db.commit()
        
        # 7. Notify user
        await update.message.reply_text(
            f"🎉 **¡Mejora Exitosa!**\n\n"
            f"Tu cuenta ahora es **{plan_id.upper()}**.\n"
            f"Disfruta de límites extendidos y mayor visibilidad.\n\n"
            f"Expira el: {expires_at.strftime('%Y-%m-%d')}",
            parse_mode="Markdown"
        )


def get_payment_handlers():
    """Return the list of handlers for registration."""
    return [
        PreCheckoutQueryHandler(pre_checkout_handler),
        MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler),
    ]
