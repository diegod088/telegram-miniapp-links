"""Activity model — maps to the 'activities' table for Pulse feed."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Integer, BigInteger, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from .user import User

class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    # Type: 'profile_creation', 'link_trending', 'vip_boost', 'new_favorite', 'milestone'
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    
    # Message to display (e.g., "User X just boosted a link!")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Metadata for deep linking in frontend
    target_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    target_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True) # 'profile', 'link'
    
    # Global visibility control
    is_public: Mapped[bool] = mapped_column(default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    user: Mapped[Optional["User"]] = relationship() # noqa: F821

    def __repr__(self) -> str:
        return f"<Activity type={self.type!r} msg={self.message[:20]}...>"
