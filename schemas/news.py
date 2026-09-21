from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NewsCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    content: str = Field(min_length=1)
    image: Optional[str] = Field(None, max_length=255)
    author: Optional[str] = Field(None, max_length=50)
    category_id: int = Field(gt=0, alias="categoryId")
    publish_time: Optional[datetime] = Field(None, alias="publishTime")

    model_config = ConfigDict(populate_by_name=True)


class NewsUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    image: Optional[str] = Field(None, max_length=255)
    author: Optional[str] = Field(None, max_length=50)
    category_id: Optional[int] = Field(None, gt=0, alias="categoryId")
    publish_time: Optional[datetime] = Field(None, alias="publishTime")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def require_at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("至少需要提供一个要修改的字段")
        non_nullable_fields = {"title", "content", "category_id", "publish_time"}
        invalid_fields = [
            field
            for field in non_nullable_fields
            if field in self.model_fields_set and getattr(self, field) is None
        ]
        if invalid_fields:
            raise ValueError(f"字段不能为 null: {', '.join(sorted(invalid_fields))}")
        return self
