"""User model — maps to the 'users' table."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tglinktree.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False, index=True
    )
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    lang_code: Mapped[str] = mapped_column(String(8), default="es")
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    ban_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    profiles: Mapped[list["Profile"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    unlocks: Mapped[list["UserUnlock"]] = relationship(  # noqa: F821
        back_populates="user"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(  # noqa: F821
        back_populates="user"
    )

    __table_args__ = (
        Index("ix_users_telegram_id", "telegram_id"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} tg={self.telegram_id}>"
