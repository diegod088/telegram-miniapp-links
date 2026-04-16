"""Async SQLAlchemy engine, session factory, and FastAPI dependency."""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from app.core.settings import get_settings

# ── Engine & Session Factory (created at import time) ─────────
_settings = get_settings()

kwargs = {}
if "sqlite" not in _settings.DATABASE_URL:
    kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
    })

engine = create_async_engine(
    _settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    **kwargs,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Declarative Base ─────────────────────────────────────────
class Base(DeclarativeBase):
    """Shared base for all ORM models."""
    pass


# ── FastAPI Dependency ───────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a DB session that auto-commits on success, rolls back on error."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
