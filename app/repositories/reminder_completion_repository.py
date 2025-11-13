"""
Reminder Completion Repository
提醒完成记录数据访问层
"""

from typing import List, Optional
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
    ) -> List[ReminderCompletion]:
        """获取某个提醒的所有完成记录"""
        return self.db.query(ReminderCompletion).filter(
            ReminderCompletion.reminder_id == reminder_id
        ).order_by(
            ReminderCompletion.completed_time.desc()
        ).offset(skip).limit(limit).all()
    
    async def get_latest_by_reminder(self, reminder_id: int) -> Optional[ReminderCompletion]:
        """获取某个提醒的最新完成记录"""
        return self.db.query(ReminderCompletion).filter(
            ReminderCompletion.reminder_id == reminder_id
        ).order_by(
            ReminderCompletion.completed_time.desc()
        ).first()
    
    async def delete_latest(self, reminder_id: int) -> bool:
        """删除最新的完成记录（用于取消完成）"""
        latest = self.get_latest_by_reminder(reminder_id)
        if latest:
            await self.db.delete(latest)
            await self.db.commit()
            return True
        return False
    
    async def count_by_reminder(self, reminder_id: int) -> int:
        """统计某个提醒的完成次数"""
        return self.db.query(ReminderCompletion).filter(
            ReminderCompletion.reminder_id == reminder_id
        ).count()
    
    async def count_by_user(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """统计用户在时间范围内的完成次数"""
        query = self.db.query(ReminderCompletion).filter(
            ReminderCompletion.user_id == user_id
        )
        
        if start_date:
            query = query.filter(ReminderCompletion.completed_time >= start_date)
        if end_date:
            query = query.filter(ReminderCompletion.completed_time <= end_date)
        
        return query.count()
