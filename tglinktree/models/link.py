"""ProfileLink model — maps to the 'profile_links' table."""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tglinktree.core.database import Base


class ProfileLink(Base):
    __tablename__ = "profile_links"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
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
    style: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    profile: Mapped["Profile"] = relationship(back_populates="links")  # noqa: F821
    locks: Mapped[list["ContentLock"]] = relationship(  # noqa: F821
        back_populates="link",
        foreign_keys="ContentLock.link_id",
    )

    __table_args__ = (
        Index("ix_profile_links_profile_position", "profile_id", "position"),
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
