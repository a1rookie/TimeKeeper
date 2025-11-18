"""
Reminder Notification Repository
提醒通知策略数据访问层
"""
from typing import List
from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.reminder_notification import ReminderNotification


class ReminderNotificationRepository:
    """提醒通知策略数据访问"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        reminder_id: int,
        advance_notify_enabled: bool = False,
        advance_days: int = 0,
        advance_notify_interval: int = 1,
        advance_notify_time: str = "09:00",
        same_day_notifications: List[str] | None = None,
        avoid_night_time: bool = True,
        night_time_fallback: str = "09:00",
        custom_message_template: str | None = None
    ) -> ReminderNotification:
        """创建通知策略"""
        notification = ReminderNotification(
            reminder_id=reminder_id,
            advance_notify_enabled=advance_notify_enabled,
            advance_days=advance_days,
            advance_notify_interval=advance_notify_interval,
            advance_notify_time=advance_notify_time,
            same_day_notifications=same_day_notifications or [],
            avoid_night_time=avoid_night_time,
            night_time_fallback=night_time_fallback,
            custom_message_template=custom_message_template,
            is_active=True
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification
    
    async def get_by_reminder_id(self, reminder_id: int) -> ReminderNotification | None:
        """根据提醒ID查询通知策略"""
        result = await self.db.execute(
            select(ReminderNotification).filter(ReminderNotification.reminder_id == reminder_id)
        )
        return result.scalar_one_or_none()
    
    async def update(
        self,
        reminder_id: int,
        **kwargs
    ) -> ReminderNotification | None:
        """更新通知策略"""
        notification = await self.get_by_reminder_id(reminder_id)
        if not notification:
            return None
        
        for key, value in kwargs.items():
            if hasattr(notification, key):
                setattr(notification, key, value)
        
        await self.db.commit()
        await self.db.refresh(notification)
        return notification
    
    async def delete(self, reminder_id: int) -> bool:
        """删除通知策略"""
        notification = await self.get_by_reminder_id(reminder_id)
        if not notification:
            return False
        
        await self.db.delete(notification)
        await self.db.commit()
        return True
    
    async def get_active_notifications(self) -> Sequence[ReminderNotification]:
        """获取所有活跃的通知策略"""
        result = await self.db.execute(
            select(ReminderNotification).filter(ReminderNotification.is_active == True)
        )
        return result.scalars().all()
