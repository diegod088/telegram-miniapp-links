"""Telegram bot — single bot replacing bot1 + bot2."""

from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

logger = logging.getLogger("app.bot")


def create_bot_application(bot_token: str, webapp_url: str):
    """
    Create and configure the python-telegram-bot Application.

    Commands:
      /start [deeplink_param] — Open Mini App
      /myprofile              — Direct link to own profile
      /help                   — Usage instructions
    """
    app = ApplicationBuilder().token(bot_token).build()

    # Store webapp_url in bot_data for handlers to access
    app.bot_data["webapp_url"] = webapp_url

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("myprofile", cmd_myprofile))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("vip", cmd_vip))

    # Payment Handlers
    from app.bot.handlers.payment_handlers import get_payment_handlers
    for handler in get_payment_handlers():
        app.add_handler(handler)

    return app


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start [deeplink_param]

    Opens the Mini App. If a deeplink param is provided (e.g., a profile slug),
    it's passed as ?startapp=<param> to the webapp URL.
    """
    webapp_url = context.bot_data.get("webapp_url", "https://example.com")

    # Check for deeplink parameter
    deeplink_param = None
    if context.args:
        deeplink_param = context.args[0]

    if deeplink_param:
        logger.info(f"Bot: /start with param '{deeplink_param}' from user {update.effective_user.id}")
        full_url = f"{webapp_url}?startapp={deeplink_param}"
    else:
        logger.info(f"Bot: /start from user {update.effective_user.id}")
        full_url = webapp_url

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🔥 Explorar Links Populares",
            web_app=WebAppInfo(url=f"{webapp_url}#/explore"),
        )],
        [InlineKeyboardButton(
            "🚀 Mi Perfil Linktree",
            web_app=WebAppInfo(url=webapp_url),
        )],
    ])

    welcome_text = (
        "👋 **¡Bienvenido a TGLinktree Social!**\n\n"
        "La primera plataforma social para descubrir y compartir "
        "los mejores canales, bots y herramientas de Telegram.\n\n"
        "🔥 **Explora** lo que es tendencia\n"
        "📈 **Vota** por tus links favoritos\n"
        "🔗 **Crea** tu propio perfil social\n\n"
        "Empieza a explorar o gestiona tu perfil 👇"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def cmd_myprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /myprofile — Direct link to the user's own profile in the Mini App.
    """
    webapp_url = context.bot_data.get("webapp_url", "https://example.com")
    logger.info(f"Bot: /myprofile from user {update.effective_user.id}")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "👤 Mi Perfil",
            web_app=WebAppInfo(url=f"{webapp_url}?startapp=myprofile"),
        )],
    ])

    await update.message.reply_text(
        "📋 Abre tu perfil para gestionar tus enlaces:",
        reply_markup=keyboard,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /help — Brief usage instructions.
    """
    help_text = (
        "ℹ️ **TGLinktree — Ayuda**\n\n"
        "Comandos disponibles:\n"
        "/start — Abrir la Mini App\n"
        "/myprofile — Ver y editar tu perfil\n"
        "/help — Mostrar esta ayuda\n\n"
        "**¿Cómo funciona?**\n"
        "1. Abre la Mini App con /start\n"
        "2. Crea tu perfil con un slug único\n"
        "3. Agrega tus enlaces\n"
        "4. Comparte tu link: t.me/BOT?start=TU_SLUG\n"
        "5. Opcionalmente, bloquea enlaces tras unirse a un canal\n\n"
        "**Planes:**\n"
        "🆓 Free — 5 enlaces, analytics 7 días\n"
        "⭐ Pro — 50 enlaces, analytics 90 días, todos los locks\n"
        "💎 Business — 500 enlaces, analytics 365 días, dominio custom"
    )

    await update.message.reply_text(help_text, parse_mode="Markdown")


async def cmd_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /vip — Show benefits and link to upgrade.
    """
    webapp_url = context.bot_data.get("webapp_url", "https://example.com")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "💎 Hacerse VIP (Pro)",
            web_app=WebAppInfo(url=f"{webapp_url}#/vip"),
        )],
        [InlineKeyboardButton(
            "💼 Plan Business",
            web_app=WebAppInfo(url=f"{webapp_url}#/vip"),
        )],
    ])

    vip_text = (
        "🌟 **¡Sé un usuario VIP de TGLinktree!** 🌟\n\n"
        "Desbloquea todo el potencial de tu perfil:\n"
        "✅ **Links Ilimitados** (Sin límite diario)\n"
        "🚀 **Boost de 24h** (Aparece en el top del feed)\n"
        "📊 **Analytics Avanzado** (Hasta 365 días)\n"
        "🔒 **Más tipos de bloqueos** (Contraseña, Pago)\n\n"
        "Mejora tu plan ahora y destaca sobre el resto 👇"
    )

    await update.message.reply_text(
        vip_text,
        reply_markup=keyboard,
        parse_mode="Markdown",
    )
