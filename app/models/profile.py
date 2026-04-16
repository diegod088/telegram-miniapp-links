"""Profile model — maps to the 'profiles' table."""

from __future__ import annotations

from typing import Optional, Any
from datetime import datetime

from sqlalchemy import Integer, BigInteger, \
    Boolean, CheckConstraint, ForeignKey, Index, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    theme: Mapped[str] = mapped_column(String(32), default="default")
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    plan: Mapped[str] = mapped_column(String(16), default="free")
    total_views: Mapped[int] = mapped_column(BigInteger, default=0)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # Monetization
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    boost_until: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    
    # Search & Discovery
    trending_score: Mapped[float] = mapped_column(default=0.0)
    boost_score: Mapped[float] = mapped_column(default=1.0)
    
    # TSVector for full-text search (Postgres only)
    search_vector: Mapped[Optional[Any]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="profiles")  # noqa: F821
    links: Mapped[list["ProfileLink"]] = relationship(  # noqa: F821
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="ProfileLink.position",
    )
    locks: Mapped[list["ContentLock"]] = relationship(  # noqa: F821
        back_populates="profile",
        foreign_keys="ContentLock.profile_id",
    )
    click_events: Mapped[list["ClickEvent"]] = relationship(  # noqa: F821
        back_populates="profile"
    )

    __table_args__ = (
        Index("ix_profiles_slug", "slug"),
        Index("ix_profiles_user_id", "user_id"),
        Index("ix_profiles_category", "category"),
        Index("ix_profiles_trending_score", "trending_score"),
    )

    def __repr__(self) -> str:
        return f"<Profile id={self.id} slug={self.slug!r}>"
