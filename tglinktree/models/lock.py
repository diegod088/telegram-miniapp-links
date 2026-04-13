"""ContentLock and UserUnlock models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tglinktree.core.database import Base


class ContentLock(Base):
    __tablename__ = "content_locks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    link_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("profile_links.id", ondelete="CASCADE"),
        nullable=True,
    )
    profile_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=True,
    )
    lock_type: Mapped[str] = mapped_column(String(32), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    link: Mapped[Optional["ProfileLink"]] = relationship(  # noqa: F821
        back_populates="locks", foreign_keys=[link_id]
    )
    profile: Mapped[Optional["Profile"]] = relationship(  # noqa: F821
        back_populates="locks", foreign_keys=[profile_id]
    )
    unlocks: Mapped[list["UserUnlock"]] = relationship(
        back_populates="lock", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "(link_id IS NOT NULL AND profile_id IS NULL) OR "
            "(link_id IS NULL AND profile_id IS NOT NULL)",
            name="ck_content_locks_exactly_one_target",
        ),
    )

    def __repr__(self) -> str:
        return f"<ContentLock id={self.id} type={self.lock_type!r}>"


class UserUnlock(Base):
    __tablename__ = "user_unlocks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lock_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("content_locks.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    unlocked_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Relationships
    lock: Mapped["ContentLock"] = relationship(back_populates="unlocks")
    user: Mapped["User"] = relationship(back_populates="unlocks")  # noqa: F821

    __table_args__ = (
        UniqueConstraint("lock_id", "user_id", name="uq_user_unlock"),
        Index("ix_user_unlocks_user_lock", "user_id", "lock_id"),
    )

    def __repr__(self) -> str:
        return f"<UserUnlock id={self.id} lock={self.lock_id} user={self.user_id}>"
