"""
PushTask Repository
推送任务数据访问层
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import and_
from datetime import datetime
from app.models.push_task import PushTask, PushStatus


class PushTaskRepository:
    """推送任务数据仓库"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, task_id: int) -> Optional[PushTask]:
        """根据ID获取推送任务"""
        result = await self.db.execute(select(PushTask).filter(PushTask.id == task_id))
        return result.scalar_one_or_none()
    
    async def get_by_reminder(
        self, 
        reminder_id: int, 
        status: Optional[PushStatus] = None
    ) -> List[PushTask]:
        """获取某个提醒的所有推送任务"""
        query = self.db.query(PushTask).filter(PushTask.reminder_id == reminder_id)
        
        if status is not None:
            query = query.filter(PushTask.status == status)
        
        return query.order_by(PushTask.scheduled_time.desc()).all()
    
    async def get_pending_tasks(self, before_time: datetime) -> List[PushTask]:
        """获取待推送的任务（计划时间在指定时间之前）"""
        return self.db.query(PushTask).filter(
            and_(
                PushTask.status == PushStatus.PENDING,
                PushTask.scheduled_time <= before_time
            )
        ).order_by(PushTask.priority.desc(), PushTask.scheduled_time).all()
    
    async def create(
        self,
        reminder_id: int,
        user_id: int,
        title: str,
        scheduled_time: datetime,
        content: Optional[str] = None,
        channels: List[str] = None,
        priority: int = 1,
        max_retries: int = 3
    ) -> PushTask:
        """创建推送任务"""
        new_task = PushTask(
            reminder_id=reminder_id,
            user_id=user_id,
            title=title,
            content=content,
            channels=channels or ["app"],
            scheduled_time=scheduled_time,
            status=PushStatus.PENDING,
            retry_count=0,
            max_retries=max_retries,
            priority=priority
        )
        
        self.db.add(new_task)
        await self.db.commit()
        await self.db.refresh(new_task)
        return new_task
    
    async def update_status(
        self, 
        task: PushTask, 
        status: PushStatus,
        error_message: Optional[str] = None,
        push_response: Optional[dict] = None
    ) -> PushTask:
        """更新任务状态"""
        task.status = status
        
        if status == PushStatus.SENT:
            task.sent_time = datetime.now()
            task.executed_at = datetime.now()
        elif status == PushStatus.FAILED:
            task.retry_count += 1
            if error_message:
                task.error_message = error_message
        
        if push_response:
            task.push_response = push_response
        
        await self.db.commit()
        await self.db.refresh(task)
        return task
    
    async def get_failed_tasks_for_retry(self, max_retries: int = 3) -> List[PushTask]:
        """获取可重试的失败任务"""
        return self.db.query(PushTask).filter(
            and_(
                PushTask.status == PushStatus.FAILED,
                PushTask.retry_count < max_retries
            )
        ).all()
    
    async def cancel_tasks_by_reminder(self, reminder_id: int) -> int:
        """取消某个提醒的所有待推送任务"""
        result = self.db.query(PushTask).filter(
            and_(
                PushTask.reminder_id == reminder_id,
                PushTask.status == PushStatus.PENDING
            )
        ).update({"status": PushStatus.CANCELLED})
        
        await self.db.commit()
        return result
    
    async def count_by_status(self, user_id: int, status: PushStatus) -> int:
        """统计用户某状态的任务数"""
        return self.db.query(PushTask).filter(
            and_(
                PushTask.user_id == user_id,
                PushTask.status == status
            )
        ).count()
