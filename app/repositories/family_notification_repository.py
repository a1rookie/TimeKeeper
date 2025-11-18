"""
Family Notification Repository
家庭通知数据访问层
"""
import asyncio
from collections.abc import Sequence
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from datetime import datetime, timezone

from app.models.family_notification import FamilyNotification, NotificationType


class FamilyNotificationRepository:
    """家庭通知数据访问"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        family_group_id: int,
        sender_id: int,
        receiver_id: int,
        notification_type: NotificationType,
        title: str,
        content: str | None = None,
        related_reminder_id: int | None = None,
        related_completion_id: int | None = None,
        metadata_json: str | None = None
    ) -> FamilyNotification:
        """创建通知"""
        notification = FamilyNotification(
            family_group_id=family_group_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            notification_type=notification_type,
            title=title,
            content=content,
            related_reminder_id=related_reminder_id,
            related_completion_id=related_completion_id,
            metadata_json=metadata_json,
            is_read=False
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification
    
    async def get_by_id(self, notification_id: int) -> FamilyNotification | None:
        """根据ID查询通知"""
        result = await self.db.execute(
            select(FamilyNotification).filter(FamilyNotification.id == notification_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> Sequence[FamilyNotification]:
        """获取用户的通知列表"""
        query = select(FamilyNotification).filter(FamilyNotification.receiver_id == user_id)
        
        if unread_only:
            query = query.filter(FamilyNotification.is_read == False)
        
        query = query.order_by(desc(FamilyNotification.created_at)).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_unread_count(self, user_id: int) -> int:
        """获取用户未读通知数量"""
        result = await self.db.execute(
            select(func.count()).select_from(FamilyNotification).filter(
                and_(
                    FamilyNotification.receiver_id == user_id,
                    FamilyNotification.is_read == False
                )
            )
        )
        return result.scalar() or 0
    
    async def mark_as_read(self, notification_id: int) -> bool:
        """标记通知为已读"""
        notification = await self.get_by_id(notification_id)
        if not notification:
            return False
        
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        await self.db.commit()
        return True
    
    async def mark_all_as_read(self, user_id: int) -> int:
        """标记用户所有通知为已读"""
        result = await self.db.execute(
            select(FamilyNotification).filter(
                and_(
                    FamilyNotification.receiver_id == user_id,
                    FamilyNotification.is_read == False
                )
            )
        )
        notifications = result.scalars().all()
        
        count = 0
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            count += 1
        
        await self.db.commit()
        return count
    
    async def delete(self, notification_id: int) -> bool:
        """删除通知"""
        notification = await self.get_by_id(notification_id)
        if not notification:
            return False
        
        await self.db.delete(notification)
        await self.db.commit()
        return True
    
    async def batch_create_for_family_members(
        self,
        family_group_id: int,
        sender_id: int,
        receiver_ids: List[int],
        notification_type: NotificationType,
        title: str,
        content: str | None = None,
        related_reminder_id: int | None = None,
        related_completion_id: int | None = None,
        metadata_json: str | None = None
    ) -> Sequence[FamilyNotification]:
        """批量为家庭成员创建通知"""
        notifications = []
        for receiver_id in receiver_ids:
            if receiver_id != sender_id:  # 不给自己发通知
                notification = FamilyNotification(
                    family_group_id=family_group_id,
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    notification_type=notification_type,
                    title=title,
                    content=content,
                    related_reminder_id=related_reminder_id,
                    related_completion_id=related_completion_id,
                    metadata_json=metadata_json,
                    is_read=False
                )
                self.db.add(notification)
                notifications.append(notification)
        
        await self.db.commit()

        await asyncio.gather(*(self.db.refresh(n) for n in notifications))
        
        return notifications
