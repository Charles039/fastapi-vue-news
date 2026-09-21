from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import notification
from models.users import User
from schemas.notification import AnnouncementCreateRequest, AnnouncementCreateResponse
from utils.auth import get_current_admin
from utils.response import success_response


router = APIRouter(prefix="/api/admin/notifications", tags=["admin-notifications"])


@router.post("/announcements")
async def create_announcement(
    data: AnnouncementCreateRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    recipient_count = await notification.create_announcement(
        db, data.title.strip(), data.content.strip()
    )
    return success_response(
        message="公告发布成功",
        data=AnnouncementCreateResponse(recipientCount=recipient_count),
    )

