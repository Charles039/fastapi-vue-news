import asyncio

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select,func,update

from cache.news_cache import (
    acquire_news_page_lock,
    get_cached_categories,
    get_cached_news_page,
    get_news_list_version,
    release_news_page_lock,
    set_cache_categories,
    set_cached_news_page,
)
from models.favorite import Favorite
from models.history import History
from models.news import Category,News
from schemas.news import NewsCreateRequest, NewsUpdateRequest
from crud.notification import (
    notify_favorited_news_deleted,
    notify_favorited_news_updated,
)

async def get_categories(db,skip:int =0,limit:int=100):
    #先尝试从新闻分类缓存中获取数据
    c=await get_cached_categories()
    if c:
        return c

    stmt=select(Category).order_by(Category.id).offset(skip).limit(limit)#新加orderby
    result=await db.execute(stmt)
    categories=result.scalars().all()#ORM结构
    #未读取到则写入缓存
    if categories:
        cat=jsonable_encoder(categories)#转格式
        await set_cache_categories(cat)
    return categories


async def _query_news_page(db: AsyncSession, category_id: int, page: int, size: int):
    offset = (page - 1) * size
    stmt = (
        select(News)
        .where(News.category_id == category_id)
        .order_by(News.id)
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(stmt)
    news_list = result.scalars().all()

    count_stmt = select(func.count(News.id)).where(News.category_id == category_id)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()
    return {
        "list": jsonable_encoder(news_list),
        "total": total,
        "hasMore": offset + len(news_list) < total,
    }


async def get_news_page(db: AsyncSession, category_id: int, page: int = 1, size: int = 10):
    """读取完整分页响应，并通过短期互斥锁避免热点缓存同时重建。"""
    version = await get_news_list_version(category_id)
    cached_page = await get_cached_news_page(category_id, page, size, version)
    if cached_page is not None:
        return cached_page

    lock_key, lock_token = await acquire_news_page_lock(
        category_id, page, size, version
    )
    if lock_token:
        try:
            # 获得锁后再次读取，避免等待锁期间缓存已被其他请求创建。
            cached_page = await get_cached_news_page(category_id, page, size, version)
            if cached_page is not None:
                return cached_page

            data = await _query_news_page(db, category_id, page, size)
            await set_cached_news_page(category_id, page, size, version, data)
            return data
        finally:
            await release_news_page_lock(lock_key, lock_token)

    # Redis 故障时不等待，直接降级查询数据库。
    if lock_token is None:
        return await _query_news_page(db, category_id, page, size)

    # 锁被其他请求持有时有限等待；等待超时后降级查询数据库。
    for _ in range(10):
        await asyncio.sleep(0.05)
        current_version = await get_news_list_version(category_id)
        cached_page = await get_cached_news_page(
            category_id, page, size, current_version
        )
        if cached_page is not None:
            return cached_page

    return await _query_news_page(db, category_id, page, size)

async def get_news_count(db:AsyncSession,category_id:int):
    #查询指定分类下的新闻数量
    stmt=select(func.count(News.id)).where(News.category_id==category_id)
    result =await db.execute(stmt)
    return result.scalar_one()    #只能有一个结果，如果有多个会报错


async def category_exists(db: AsyncSession, category_id: int):
    stmt = select(Category.id).where(Category.id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def create_news(db: AsyncSession, data: NewsCreateRequest):
    if not await category_exists(db, data.category_id):
        return None

    values = data.model_dump(exclude_none=True, by_alias=False)
    news_item = News(**values)
    db.add(news_item)
    await db.commit()
    await db.refresh(news_item)
    return news_item


async def update_news(db: AsyncSession, news_id: int, data: NewsUpdateRequest):
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    news_item = result.scalar_one_or_none()
    if news_item is None:
        return None, None

    values = data.model_dump(exclude_unset=True, by_alias=False)
    new_category_id = values.get("category_id")
    if new_category_id is not None and not await category_exists(db, new_category_id):
        return news_item, False

    old_category_id = news_item.category_id
    for field, value in values.items():
        setattr(news_item, field, value)

    # 新闻变化与通知写入共用一次提交，任一失败都会由 get_db 回滚。
    await notify_favorited_news_updated(db, news_item)
    await db.commit()
    await db.refresh(news_item)
    return news_item, old_category_id


async def delete_news(db: AsyncSession, news_id: int):
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    news_item = result.scalar_one_or_none()
    if news_item is None:
        return None

    category_id = news_item.category_id
    # 必须先保存收藏用户名单和标题快照，再删除收藏及新闻。
    await notify_favorited_news_deleted(db, news_item)
    await db.execute(delete(Favorite).where(Favorite.news_id == news_id))
    await db.execute(delete(History).where(History.news_id == news_id))
    await db.delete(news_item)
    await db.commit()
    return category_id


async def get_news_detail(db:AsyncSession,news_id:int):
    #查询指定id的新闻
    stmt=select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()#能查到就返回内容，否则返回None

async def increase_news_views(db:AsyncSession,news_id:int):
    #更新新闻浏览量
   stmt= update(News).where(News.id==news_id).values(views=News.views+1)
   result=await db.execute(stmt)#返回了一个ORM对象
   await db.commit()   #更新立刻提交给数据库
   #更新->检查数据库是否真的命中数据->命中返回True
   return result.rowcount>0#命中行数

async def get_related_news(db:AsyncSession,news_id:int,category_id:int,limit:int=5):
    #推荐相关新闻
    stmt=select(News).where(
        News.category_id==category_id,
        News.id != news_id
    ).order_by(
        News.views.desc(),   #desc降序排列
        News.publish_time.desc()
    ).limit(limit)#按发布时间排序
    result=await db.execute(stmt)
    related_news= result.scalars().all() #这是所有的
    #列表推导式 推导出新闻的核心数据，然后再RETURN
    return [{   "id":news_detail.id,
                "title":news_detail.title,
                "content":news_detail.content,
                "image":news_detail.image,
                "author":news_detail.author,
                "publishTime":news_detail.publish_time,
                "categoryId":news_detail.category_id,
                "views":news_detail.views,

    }for news_detail in related_news]
