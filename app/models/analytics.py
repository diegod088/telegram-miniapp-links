"""ClickEvent model — maps to the 'click_events' table."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, BigInteger, Integer, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from .profile import Profile


class ClickEvent(Base):
    __tablename__ = "click_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    link_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("profile_links.id", ondelete="SET NULL"),
        nullable=True,
    )
    visitor_tg_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    referrer: Mapped[str | None] = mapped_column(String(256), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    profile: Mapped["Profile"] = relationship(back_populates="click_events")  # noqa: F821

    __table_args__ = (
        Index("ix_click_events_profile_created", "profile_id", "created_at"),
        Index("ix_click_events_link_created", "link_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ClickEvent id={self.id} type={self.event_type!r}>"
