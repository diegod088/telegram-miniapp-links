"""ProfileLink model — maps to the 'profile_links' table."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, BigInteger, Boolean, DateTime, ForeignKey, Index, SmallInteger, String, Text, func
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tglinktree.core.database import Base


class ProfileLink(Base):
    __tablename__ = "profile_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    position: Mapped[int] = mapped_column(SmallInteger, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    link_type: Mapped[str] = mapped_column(String(32), default="url")
    style: Mapped[dict] = mapped_column(JSON, default=dict)

    # Social Fields
    category: Mapped[str] = mapped_column(String(32), default="OTHER", index=True)
    canonical_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    upvotes: Mapped[int] = mapped_column(Integer, default=0)
    views: Mapped[int] = mapped_column(Integer, default=0)
    is_sponsored: Mapped[bool] = mapped_column(Boolean, default=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    report_count: Mapped[int] = mapped_column(Integer, default=0)
    boosted_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    profile: Mapped["Profile"] = relationship(back_populates="links")  # noqa: F821
    locks: Mapped[list["ContentLock"]] = relationship(  # noqa: F821
        back_populates="link",
        foreign_keys="ContentLock.link_id",
    )

    __table_args__ = (
        Index("ix_profile_links_profile_position", "profile_id", "position"),
        Index("ix_profile_links_category", "category"),
    )

    @property
    def is_locked(self) -> bool:
        # Avoid lazy-load missing greenlet if locks wasn't explicitly loaded
        from sqlalchemy.orm.attributes import instance_state
        if "locks" in instance_state(self).unloaded:
            return False
        return any(lock.is_active for lock in self.locks)

    def __repr__(self) -> str:
        return f"<ProfileLink id={self.id} title={self.title!r}>"


class LinkUpvote(Base):
    """Many-to-Many association for User upvotes on Links."""
    __tablename__ = "user_link_upvotes"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    link_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("profile_links.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    user: Mapped["User"] = relationship()  # noqa: F821
    link: Mapped["ProfileLink"] = relationship()

    __table_args__ = (
        Index("ix_user_link_upvotes_user_link", "user_id", "link_id"),
    )

    def __repr__(self) -> str:
        return f"<LinkUpvote user={self.user_id} link={self.link_id}>"
