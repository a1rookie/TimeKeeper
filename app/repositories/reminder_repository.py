"""
Reminder Repository
提醒数据访问层 - 异步版本
"""

from typing import List, Any
from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from datetime import datetime
from app.models.reminder import Reminder, ReminderCategory, RecurrenceType


class ReminderRepository:
    """提醒数据仓库"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, reminder_id: int, user_id: int) -> Reminder | None:
        """根据ID获取提醒（验证所有权）"""
        result = await self.db.execute(
            select(Reminder).filter(
                and_(
                    Reminder.id == reminder_id,
                    Reminder.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_id_without_user_check(self, reminder_id: int) -> Reminder | None:
        """根据ID获取提醒（不验证所有权，用于家庭共享提醒）"""
        result = await self.db.execute(
            select(Reminder).where(Reminder.id == reminder_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_reminders(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        is_active: bool | None = None,
        category: ReminderCategory | None = None
    ) -> Sequence[Reminder]:
        """获取用户的提醒列表"""
        query = select(Reminder).filter(Reminder.user_id == user_id)
        
        if is_active is not None:
            query = query.filter(Reminder.is_active == is_active)
        
        if category is not None:
            query = query.filter(Reminder.category == category)
        
        query = query.order_by(Reminder.next_remind_time).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def create(
        self,
        user_id: int,
        title: str,
        category: ReminderCategory,
        recurrence_type: RecurrenceType,
        first_remind_time: datetime,
        description: str | None = None,
        recurrence_config: dict | None = None,
        remind_channels: List[str] | None= None,
        advance_minutes: int = 0,
        priority: int = 1,
        amount: int | None = None,
        location: dict | None = None,
        attachments: list | None = None
    ) -> Reminder:
        """创建新提醒"""
        new_reminder = Reminder(
            user_id=user_id,
            title=title,
            description=description,
            category=category,
            recurrence_type=recurrence_type,
            recurrence_config=recurrence_config or {},
            first_remind_time=first_remind_time,
            next_remind_time=first_remind_time,
            remind_channels=remind_channels or ["app"],
            advance_minutes=advance_minutes,
            priority=priority,
            amount=amount,
            location=location,
            attachments=attachments
        )
        
        self.db.add(new_reminder)
        await self.db.commit()
        await self.db.refresh(new_reminder)
        return new_reminder


    async def update(self, reminder: Reminder, **kwargs: Any) -> Reminder:
        """更新提醒"""
        for field, value in kwargs.items():
            if hasattr(reminder, field) and value is not None:
                setattr(reminder, field, value)
        
        await self.db.commit()
        await self.db.refresh(reminder)
        return reminder
    
    async def delete(self, reminder: Reminder) -> None:
        """删除提醒"""
        await self.db.delete(reminder)
        await self.db.commit()
    
    async def mark_completed(self, reminder: Reminder, user_id: int) -> Reminder:
        """标记提醒为已完成，并返回更新后的提醒"""
        reminder.is_completed = True
        reminder.completed_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(reminder)
        return reminder
    
    async def mark_uncompleted(self, reminder: Reminder) -> Reminder:
        """取消完成状态"""
        reminder.is_completed = False
        reminder.completed_at = None
        await self.db.commit()
        await self.db.refresh(reminder)
        return reminder
    
    async def update_next_remind_time(self, reminder: Reminder, next_time: datetime) -> Reminder:
        """更新下次提醒时间"""
        reminder.next_remind_time = next_time
        reminder.last_remind_time = reminder.completed_at or datetime.now()
        await self.db.commit()
        await self.db.refresh(reminder)
        return reminder
    
    async def get_pending_reminders(self, before_time: datetime) -> Sequence[Reminder]:
        """获取待推送的提醒（下次提醒时间在指定时间之前且未完成）"""
        result = await self.db.execute(
            select(Reminder).filter(
                and_(
                    Reminder.is_active == True,
                    Reminder.is_completed == False,
                    Reminder.next_remind_time <= before_time
                )
            )
        )
        return result.scalars().all()
    
    async def count_user_reminders(self, user_id: int, is_active: bool | None = None) -> int | None:
        """统计用户提醒数量"""
        from sqlalchemy import func, select as sql_select
        
        query = sql_select(func.count()).select_from(Reminder).filter(Reminder.user_id == user_id)
        
        if is_active is not None:
            query = query.filter(Reminder.is_active == is_active)
        
        result = await self.db.execute(query)
        return result.scalar()
