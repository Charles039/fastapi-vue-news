
#定义模型类文件  定义pydantic模型类才能传递请求体参数

from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, Index, Integer, String, Enum, DateTime, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class User(Base):
    __tablename__ = 'user'

    # 创建索引
    __table_args__ = (
        Index('username_UNIQUE', 'username'),
        Index('phone_UNIQUE', 'phone'),#phone已经去除unique了，否则无法创建用户
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="用户名")
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码（加密存储）")
    nickname: Mapped[Optional[str]] = mapped_column(String(50), comment="昵称")
    avatar: Mapped[Optional[str]] = mapped_column(String(255), comment="头像URL",
                                                  default='https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg')
    gender: Mapped[Optional[str]] = mapped_column(Enum('male', 'female', 'unknown'), comment="性别", default='unknown')
    bio: Mapped[Optional[str]] = mapped_column(String(500), comment="个人简介", default='这个人很懒，什么都没留下')
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=False, comment="手机号")
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
        comment="是否为管理员"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), onupdate=datetime.now(),
                                                 comment="更新时间")
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', nickname='{self.nickname}')>"


class UserToken(Base):
    __tablename__ = 'user_token'
    # 创建索引
    __table_args__ = (
        Index('token_UNIQUE', 'token'),
        Index('fk_user_token_user_idx', 'user_id'),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="令牌ID")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False, comment="用户ID")
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, comment="令牌值")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="过期时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), comment="创建时间")


    def __repr__(self):
        return f"<UserToken(id={self.id}, user_id={self.user_id}, token='{self.token}')>"
