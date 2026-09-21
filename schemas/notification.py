from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnnouncementCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=5000)

    @field_validator("title", "content")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("内容不能为空")
        return value


class NotificationItemResponse(BaseModel):
    id: int
    type: str
    title: str
    content: str
    news_id: int | None = Field(None, alias="newsId")
    news_title: str | None = Field(None, alias="newsTitle")
    is_read: bool = Field(alias="isRead")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class NotificationListResponse(BaseModel):
    list: list[NotificationItemResponse]
    total: int
    has_more: bool = Field(alias="hasMore")
    unread_count: int = Field(alias="unreadCount")

    model_config = ConfigDict(populate_by_name=True)


class UnreadCountResponse(BaseModel):
    unread_count: int = Field(alias="unreadCount")

    model_config = ConfigDict(populate_by_name=True)


class AnnouncementCreateResponse(BaseModel):
    recipient_count: int = Field(alias="recipientCount")

    model_config = ConfigDict(populate_by_name=True)
