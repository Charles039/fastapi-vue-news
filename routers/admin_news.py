from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from cache.news_cache import invalidate_news_category
from config.db_conf import get_db
from crud import news
from models.users import User
from schemas.news import NewsCreateRequest, NewsUpdateRequest
from utils.auth import get_current_admin
from utils.response import success_response


router = APIRouter(prefix="/api/admin/news", tags=["admin-news"])


@router.post("")
async def create_news(
    data: NewsCreateRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    news_item = await news.create_news(db, data)
    if news_item is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定的新闻分类不存在",
        )

    await invalidate_news_category(news_item.category_id)
    return success_response(message="新增新闻成功", data=jsonable_encoder(news_item))


@router.patch("/{news_id}")
async def update_news(
    news_id: int,
    data: NewsUpdateRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    news_item, old_category_id = await news.update_news(db, news_id, data)
    if news_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="新闻不存在",
        )
    if old_category_id is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定的新闻分类不存在",
        )

    await invalidate_news_category(old_category_id)
    if news_item.category_id != old_category_id:
        await invalidate_news_category(news_item.category_id)
    return success_response(message="修改新闻成功", data=jsonable_encoder(news_item))


@router.delete("/{news_id}")
async def delete_news(
    news_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    category_id = await news.delete_news(db, news_id)
    if category_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="新闻不存在",
        )

    await invalidate_news_category(category_id)
    return success_response(message="删除新闻成功")
