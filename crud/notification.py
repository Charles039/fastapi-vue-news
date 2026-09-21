from datetime import datetime
import uuid

from sqlalchemy import delete, false, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.notification import Notification
from models.users import User


ANNOUNCEMENT = "announcement"
NEWS_UPDATED = "news_updated"
NEWS_DELETED = "news_deleted"


def _is_unread():
    # SQL Server 的 BIT 字段必须使用“= 0”；Column.is_(False) 会生成无效的“IS 0”。
    return Notification.is_read == false()


async def create_announcement(
    db: AsyncSession, title: str, content: str
) -> int:
    result = await db.execute(select(User.id))
    user_ids = result.scalars().all()
    announcement_key = f"announcement:{uuid.uuid4()}"
    db.add_all(
        Notification(
            user_id=user_id,
            type=ANNOUNCEMENT,
            title=title,
            content=content,
            dedupe_key=announcement_key,
        )
        for user_id in user_ids
    )
    await db.commit()
    return len(user_ids)


async def _favorite_user_ids(db: AsyncSession, news_id: int) -> list[int]:
    result = await db.execute(
        select(Favorite.user_id).where(Favorite.news_id == news_id)
    )
    return list(result.scalars().all())


async def notify_favorited_news_updated(db: AsyncSession, news_item) -> int:
    user_ids = await _favorite_user_ids(db, news_item.id)
    if not user_ids:
        return 0

    dedupe_key = f"news:{news_item.id}:updated"
    result = await db.execute(
        select(Notification).where(
            Notification.user_id.in_(user_ids),
            Notification.dedupe_key == dedupe_key,
        )
    )
    existing = {item.user_id: item for item in result.scalars().all()}
    now = datetime.now()
    for user_id in user_ids:
        content = f"你收藏的新闻《{news_item.title}》内容已更新。"
        item = existing.get(user_id)
        if item is None:
            db.add(
                Notification(
                    user_id=user_id,
                    type=NEWS_UPDATED,
                    title="收藏新闻已更新",
                    content=content,
                    news_id=news_item.id,
                    news_title=news_item.title,
                    dedupe_key=dedupe_key,
                )
            )
        else:
            item.title = "收藏新闻已更新"
            item.content = content
            item.news_title = news_item.title
            item.is_read = False
            item.updated_at = now
    return len(user_ids)


async def notify_favorited_news_deleted(db: AsyncSession, news_item) -> int:
    user_ids = await _favorite_user_ids(db, news_item.id)
    await db.execute(
        delete(Notification).where(
            Notification.news_id == news_item.id,
            Notification.type == NEWS_UPDATED,
        )
    )
    if not user_ids:
        return 0

    dedupe_key = f"news:{news_item.id}:deleted"
    result = await db.execute(
        select(Notification).where(
            Notification.user_id.in_(user_ids),
            Notification.dedupe_key == dedupe_key,
        )
    )
    existing = {item.user_id: item for item in result.scalars().all()}
    now = datetime.now()
    for user_id in user_ids:
        content = f"你收藏的新闻《{news_item.title}》已被删除，无法再查看详情。"
        item = existing.get(user_id)
        if item is None:
            db.add(
                Notification(
                    user_id=user_id,
                    type=NEWS_DELETED,
                    title="收藏新闻已删除",
                    content=content,
                    news_id=news_item.id,
                    news_title=news_item.title,
                    dedupe_key=dedupe_key,
                )
            )
        else:
            item.content = content
            item.news_title = news_item.title
            item.is_read = False
            item.updated_at = now
    return len(user_ids)


async def get_notification_list(
    db: AsyncSession, user_id: int, page: int = 1, page_size: int = 20
):
    offset = (page - 1) * page_size
    total = await db.scalar(
        select(func.count(Notification.id)).where(Notification.user_id == user_id)
    )
    unread_count = await get_unread_count(db, user_id)
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.updated_at.desc(), Notification.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    return result.scalars().all(), total or 0, unread_count


async def get_unread_count(db: AsyncSession, user_id: int) -> int:
    count = await db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            _is_unread(),
        )
    )
    return count or 0


async def mark_notification_read(
    db: AsyncSession, user_id: int, notification_id: int
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        return None
    item.is_read = True
    await db.commit()
    await db.refresh(item)
    return item


async def mark_all_notifications_read(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, _is_unread())
        .values(is_read=True)
    )
    await db.commit()
    return result.rowcount or 0


async def delete_notification(
    db: AsyncSession, user_id: int, notification_id: int
) -> bool:
    result = await db.execute(
        delete(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    await db.commit()
    return result.rowcount > 0


async def clear_notifications(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        delete(Notification).where(Notification.user_id == user_id)
    )
    await db.commit()
    return result.rowcount or 0
