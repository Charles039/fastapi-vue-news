#新闻相关的缓存方法：新闻分类的读取和写入
#key-value
from typing import List, Dict, Any, Optional

from config.cache_conf import (
    acquire_lock,
    get_cache,
    get_json_cache,
    increment_cache,
    release_lock,
    set_cache,
)

CATE_KEY="news:categories"
NEWS_LIST="news:list"
NEWS_VERSION="news:category"
#获取新闻分类缓存（提取列表或字典）
async def get_cached_categories():
    return await get_json_cache(CATE_KEY)
#写入新闻分类缓存:缓存的数据、过期时间
#分类、配置7200,列表600,详情1800,验证码120  --数据越稳定，缓存越持久
async def set_cache_categories(data:List[Dict[str,Any]],expire:int=7200):
    return await set_cache(CATE_KEY,data,expire)

def _version_key(category_id: int):
    return f"{NEWS_VERSION}:{category_id}:version"


async def get_news_list_version(category_id: int):
    value = await get_cache(_version_key(category_id))
    try:
        return int(value) if value is not None else 0
    except (TypeError, ValueError):
        return 0


def build_news_page_key(category_id: int, page: int, size: int, version: int):
    return f"{NEWS_LIST}:category:{category_id}:v{version}:page:{page}:size:{size}"


def build_news_page_lock_key(category_id: int, page: int, size: int, version: int):
    return f"lock:{build_news_page_key(category_id, page, size, version)}"


# 缓存完整分页响应：list、total、hasMore 使用同一个版本，命中后不再查询数据库。
async def get_cached_news_page(category_id: int, page: int, size: int, version: int):
    key = build_news_page_key(category_id, page, size, version)
    return await get_json_cache(key)


async def set_cached_news_page(
    category_id: int,
    page: int,
    size: int,
    version: int,
    data: Dict[str, Any],
    expire: int = 1800,
):
    key = build_news_page_key(category_id, page, size, version)
    return await set_cache(key, data, expire)


async def invalidate_news_category(category_id: int):
    """切换分类缓存版本；旧版本键由 TTL 自动清理。"""
    return await increment_cache(_version_key(category_id))


async def acquire_news_page_lock(
    category_id: int, page: int, size: int, version: int, expire: int = 10
):
    key = build_news_page_lock_key(category_id, page, size, version)
    token = await acquire_lock(key, expire)
    return key, token


async def release_news_page_lock(key: str, token: str):
    return await release_lock(key, token)
