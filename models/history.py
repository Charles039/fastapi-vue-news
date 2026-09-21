from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, DateTime, ForeignKey, Index
from datetime import datetime

from models.base import Base

#浏览历史表ORM模型
class History(Base):
    __tablename__ = 'history'
    # 创建索引
    __table_args__ = (
        Index('fk_history_user_idx', 'user_id'),
        Index('fk_history_news_idx', 'news_id'),
        Index('idx_view_time', 'view_time'),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="历史ID")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False, comment="用户ID")
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey("news.id"), nullable=False, comment="新闻ID")
    view_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, comment="浏览时间")

    def __repr__(self):
        return f"<History(id={self.id}, user_id={self.user_id}, news_id={self.news_id}, view_time={self.view_time})>"
