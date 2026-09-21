from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, UniqueConstraint, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Notification(Base):
    __tablename__ = "notification"
    __table_args__ = (
        UniqueConstraint("user_id", "dedupe_key", name="uq_notification_user_dedupe"),
        Index("idx_notification_user_time", "user_id", "updated_at"),
        Index("idx_notification_user_unread", "user_id", "is_read"),
        Index("idx_notification_news", "news_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    news_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    news_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(100), nullable=False)
    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

