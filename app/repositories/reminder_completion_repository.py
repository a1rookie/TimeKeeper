"""
Reminder Completion Repository
提醒完成记录数据访问层
"""

from typing import List, Optional
from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.models.reminder_completion import ReminderCompletion


class ReminderCompletionRepository:
    """提醒完成记录数据仓库"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        reminder_id: int,
        user_id: int,
        scheduled_time: Optional[datetime] = None,
        note: Optional[str] = None,
        status: str = "completed"
    ) -> ReminderCompletion:
        """创建完成记录"""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        delay = 0
        if scheduled_time:
            # 确保scheduled_time有时区信息
            if scheduled_time.tzinfo is None:
                from app.core.config import settings
                scheduled_time = scheduled_time.replace(tzinfo=timezone.utc)
            delay = int((now - scheduled_time).total_seconds() / 60)
        
        completion = ReminderCompletion(
            reminder_id=reminder_id,
            user_id=user_id,
            scheduled_time=scheduled_time,
            completed_time=now,
            status=status,
            delay_minutes=delay,
            note=note
        )
        
        self.db.add(completion)
        await self.db.commit()
        await self.db.refresh(completion)
        return completion
    
    async def get_by_reminder(
        self,
        reminder_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[ReminderCompletion]:
        """获取某个提醒的所有完成记录"""
        stmt = select(ReminderCompletion).where(
            ReminderCompletion.reminder_id == reminder_id
        ).order_by(
            ReminderCompletion.completed_time.desc()
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_latest_by_reminder(self, reminder_id: int) -> ReminderCompletion | None:
        """获取某个提醒的最新完成记录"""
        stmt = select(ReminderCompletion).where(
            ReminderCompletion.reminder_id == reminder_id
        ).order_by(
            ReminderCompletion.completed_time.desc()
        ).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def delete_latest(self, reminder_id: int) -> bool:
        """删除最新的完成记录（用于取消完成）"""
        latest = await self.get_latest_by_reminder(reminder_id)
        if latest:
            await self.db.delete(latest)
            await self.db.commit()
            return True
        return False
    
    async def count_by_reminder(self, reminder_id: int) -> int:
        """统计某个提醒的完成次数"""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(ReminderCompletion).where(
            ReminderCompletion.reminder_id == reminder_id
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
    
    async def count_by_user(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """统计用户在时间范围内的完成次数"""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(ReminderCompletion).where(
            ReminderCompletion.user_id == user_id
        )
        
        if start_date:
            stmt = stmt.where(ReminderCompletion.completed_time >= start_date)
        if end_date:
            stmt = stmt.where(ReminderCompletion.completed_time <= end_date)
        
        result = await self.db.execute(stmt)
        return result.scalar() or 0
    
    async def check_recent_completion(
        self,
        reminder_id: int,
        scheduled_time: datetime,
        time_window_hours: int = 1
    ) -> ReminderCompletion | None:
        """检查最近是否有完成记录（防重复）"""
        from datetime import timedelta
        time_window = timedelta(hours=time_window_hours)
        stmt = select(ReminderCompletion).where(
            ReminderCompletion.reminder_id == reminder_id,
            ReminderCompletion.scheduled_time >= scheduled_time - time_window,
            ReminderCompletion.scheduled_time <= scheduled_time + time_window
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_user_since(
        self,
        user_id: int,
        since: datetime,
        limit: int = 1000
    ) -> Sequence[ReminderCompletion]:
        """获取用户指定时间后的完成记录"""
        stmt = select(ReminderCompletion).where(
            ReminderCompletion.user_id == user_id,
            ReminderCompletion.completed_time >= since
        ).order_by(
            ReminderCompletion.completed_time.desc()
        ).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
