from pydantic import BaseModel,Field,ConfigDict
from datetime import datetime
from schemas.base import NewsItemBase


class FavoriteCheckResponse(BaseModel):
    is_favorite:bool=Field(alias="isFavorite")

class FavoritedAddRequest(BaseModel):
    news_id:int=Field(alias="newsId")

#规划两个类：新闻模型类加收藏模型类
class FavoriteNewsItemResponse(NewsItemBase):
    favorite_id: int=Field(alias="favoriteId")#别名是前端约定的
    favorite_time:datetime=Field(alias="favoriteTime")
    model_config = ConfigDict(
        populate_by_name=True,  # 别名跟字段名兼容
        from_attributes=True  # 允许从ORM提取属性值
    )
#收藏列表接口响应的模型类
class FavoriteListResponse(BaseModel):
    list:list[FavoriteNewsItemResponse]
    total:int
    has_more:bool=Field(alias="hasMore")#hasMore是跟前端约定的
    model_config=ConfigDict(
        populate_by_name=True,#别名跟字段名兼容
        from_attributes=True#允许从ORM提取属性值
    )