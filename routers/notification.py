from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import notification
from models.users import User
from schemas.notification import (
    NotificationItemResponse,
    NotificationListResponse,
    UnreadCountResponse,
)
from utils.auth import get_current_user
from utils.response import success_response


router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows, total, unread_count = await notification.get_notification_list(
        db, user.id, page, page_size
    )
    data = NotificationListResponse(
        list=[NotificationItemResponse.model_validate(item) for item in rows],
        total=total,
        hasMore=page * page_size < total,
        unreadCount=unread_count,
    )
    return success_response(message="获取通知列表成功", data=data)


@router.get("/unread-count")
async def get_unread_count(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await notification.get_unread_count(db, user.id)
    return success_response(
        message="获取未读数量成功",
        data=UnreadCountResponse(unreadCount=count),
    )


@router.patch("/read-all")
async def mark_all_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await notification.mark_all_notifications_read(db, user.id)
    return success_response(message=f"已将{count}条通知标记为已读")


@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await notification.mark_notification_read(db, user.id, notification_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="通知不存在")
    return success_response(
        message="通知已读", data=NotificationItemResponse.model_validate(item)
    )


@router.delete("/{notification_id}")
async def remove_notification(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await notification.delete_notification(db, user.id, notification_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="通知不存在")
    return success_response(message="删除通知成功")


@router.delete("")
async def clear_notifications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await notification.clear_notifications(db, user.id)
    return success_response(message=f"清空了{count}条通知")

