"""FastAPI application entry point with lifespan management."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from tglinktree.config import get_settings
from tglinktree.core.database import engine
from tglinktree.core.exceptions import register_exception_handlers
from tglinktree.core.redis import close_redis, init_redis

# Import all models so SQLAlchemy registers them
from tglinktree.models import *  # noqa: F401, F403

from tglinktree.api.routers.profiles import router as profiles_router
from tglinktree.api.routers.links import router as links_router
from tglinktree.api.routers.locks import router as locks_router
from tglinktree.api.routers.discovery import router as discovery_router
from tglinktree.api.routers.analytics import router as analytics_router
from tglinktree.api.routers.payments import router as payments_router

logger = logging.getLogger("tglinktree")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup/shutdown lifecycle.
    - Initializes Redis
    - Starts the Telegram bot in a background task
    - Cleans up on shutdown
    """
    settings = get_settings()

    # ── Startup ──────────────────────────────────────────
    logger.info("Starting up TGLinktree...")

    # 1. Init Redis
    await init_redis()
    logger.info("Redis connected.")

    # 2. Start bot in background
    bot_task = None
    try:
        from tglinktree.bot import create_bot_application

        bot_app = create_bot_application(settings.BOT_TOKEN, settings.WEBAPP_URL)

        async def run_bot():
            """Run the bot polling in background."""
            try:
                await bot_app.initialize()
                await bot_app.start()
                await bot_app.updater.start_polling(drop_pending_updates=True)
                logger.info(f"Telegram bot started polling.")
                # Keep alive until cancelled
                while True:
                    await asyncio.sleep(3600)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Bot error: {e}")

        bot_task = asyncio.create_task(run_bot())
        logger.info("Bot background task created.")
    except Exception as e:
        logger.warning(f"Could not start bot: {e}")

    yield

    # ── Shutdown ─────────────────────────────────────────
    logger.info("Shutting down TGLinktree...")

    # Stop bot
    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass
        try:
            await bot_app.updater.stop()
            await bot_app.stop()
            await bot_app.shutdown()
        except Exception:
            pass

    # Close Redis
    await close_redis()

    # Dispose DB engine
    await engine.dispose()

    logger.info("Shutdown complete.")


# ── Create App ────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="TGLinktree",
        description="Linktree for Telegram — Create your profile, share your links.",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS — restrict to known origins in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.WEBAPP_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Include routers under /api prefix
    app.include_router(profiles_router, prefix="/api")
    app.include_router(links_router, prefix="/api")
    app.include_router(locks_router, prefix="/api")
    app.include_router(discovery_router, prefix="/api")
    app.include_router(analytics_router, prefix="/api")
    app.include_router(payments_router, prefix="/api")

    # Health check
    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "1.0.0"}

    # Serve index.html with BOT_USERNAME injected
    import os
    from fastapi.responses import HTMLResponse

    public_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
    index_path = os.path.join(public_dir, "index.html")

    @app.get("/", response_class=HTMLResponse)
    async def serve_index():
        with open(index_path, "r", encoding="utf-8") as f:
            html = f.read()
        html = html.replace("BOT_USERNAME_PLACEHOLDER", settings.BOT_USERNAME or "TelegramTreeBot")
        return HTMLResponse(content=html, media_type="text/html; charset=utf-8")

    # Mount static files for any other assets (favicon, etc.)
    app.mount("/", StaticFiles(directory=public_dir, html=False), name="public")

    return app


app = create_app()
