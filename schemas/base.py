from pydantic import BaseModel,Field,ConfigDict
from typing import Optional
from datetime import datetime

class NewsItemBase(BaseModel):
    id:int
    title:str
    description:Optional[str]=None
    image:Optional[str]=None
    author:Optional[str]=None
    category_id:int=Field(alias="categoryId")
    views:int
    publish_time:Optional[datetime]=Field(None,alias="publishedTime")
    model_config=ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )