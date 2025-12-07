"""
Family Notification API
家庭通知的 API 路由
"""
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.notification import FamilyNotificationResponse, NotificationStats
from app.repositories.family_notification_repository import FamilyNotificationRepository

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=ApiResponse[List[FamilyNotificationResponse]])
async def get_my_notifications(
    unread_only: bool = Query(False, description="仅查询未读通知"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ApiResponse[List[FamilyNotificationResponse]]:
    """
    获取我的通知列表
    """
    notification_repo = FamilyNotificationRepository(db)
    user_id = int(current_user.id)  
    notifications = await notification_repo.get_user_notifications(
        user_id= user_id,
        unread_only=unread_only,
        limit=limit,
        offset=offset
    )
    
    logger.info(
        "get_notifications",
        user_id=current_user.id,
        unread_only=unread_only,
        count=len(notifications)
    )
    
    return ApiResponse[List[FamilyNotificationResponse]].success(data=[
        FamilyNotificationResponse.model_validate(n) for n in notifications
    ])


@router.get("/stats", response_model=ApiResponse[NotificationStats])
async def get_notification_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ApiResponse[NotificationStats]:
    """
    获取通知统计信息
    """
    notification_repo = FamilyNotificationRepository(db)
    user_id = int(current_user.id)  
    all_notifications = await notification_repo.get_user_notifications(
        user_id=user_id,
        unread_only=False,
        limit=1000
    )
    unread_count = await notification_repo.get_unread_count(user_id=user_id)
    
    return ApiResponse[NotificationStats].success(data=NotificationStats(
        total_count=len(all_notifications),
        unread_count=unread_count
    ))


@router.post("/{notification_id}/read", response_model=ApiResponse[FamilyNotificationResponse])
async def mark_notification_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ApiResponse[FamilyNotificationResponse]:
    """
    标记通知为已读
    """
    notification_repo = FamilyNotificationRepository(db)
    notification = await notification_repo.get_by_id(notification_id)
    user_id = int(current_user.id)  
    receiver_id = int(notification.receiver_id) if notification else None 
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在"
        )
    
    if receiver_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此通知"
        )
    
    success = await notification_repo.mark_as_read(notification_id)
    
    if success:
        notification = await notification_repo.get_by_id(notification_id)
        logger.info(
            "notification_marked_read",
            notification_id=notification_id,
            user_id=current_user.id
        )
        return ApiResponse[FamilyNotificationResponse].success(
            data=FamilyNotificationResponse.model_validate(notification),
            message="已标记为已读"
        )
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="标记失败"
    )


@router.post("/read-all", response_model=ApiResponse[Dict[str, int]])
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ApiResponse[Dict[str, int]]:
    """
    标记所有通知为已读
    """
    user_id = int(current_user.id)  
    notification_repo = FamilyNotificationRepository(db)
    count = await notification_repo.mark_all_as_read(user_id=user_id)
    
    logger.info(
        "all_notifications_marked_read",
        user_id=current_user.id,
        count=count
    )
    
    return ApiResponse[Dict[str, int]].success(
        data={"marked_count": count},
        message=f"已标记 {count} 条通知为已读"
    )


@router.delete("/{notification_id}", response_model=ApiResponse[None])
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ApiResponse[None]:
    """
    删除通知
    """
    notification_repo = FamilyNotificationRepository(db)
    notification = await notification_repo.get_by_id(notification_id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在"
        )
    user_id = int(current_user.id)  
    receiver_id = int(notification.receiver_id) if notification else None 

    if receiver_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此通知"
        )
    
    success = await notification_repo.delete(notification_id)
    
    if success:
        logger.info(
            "notification_deleted",
            notification_id=notification_id,
            user_id=current_user.id
        )
        return ApiResponse[None].success(message="通知已删除")
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="删除失败"
    )
