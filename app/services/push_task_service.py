"""
PushTask Service
推送任务服务 - 负责自动生成和管理推送任务
"""

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional
from app.models.reminder import Reminder
from app.models.push_task import PushTask, PushStatus
from app.core.recurrence import calculate_next_occurrence


async def create_push_task_for_reminder(db: AsyncSession, reminder: Reminder) -> Optional[PushTask]:
    """
    为提醒创建推送任务
    
    Args:
        db: 数据库会话
        reminder: 提醒对象
    
    Returns:
        创建的推送任务对象，如果提醒未激活则返回None
    """
    if not reminder.is_active:
        return None
    
    # 计算推送时间（提前advance_minutes分钟）
    scheduled_time = reminder.next_remind_time
    if reminder.advance_minutes > 0:
        scheduled_time = scheduled_time - timedelta(minutes=reminder.advance_minutes)
    
    # 创建推送任务
    push_task = PushTask(
        reminder_id=reminder.id,
        user_id=reminder.user_id,
        title=reminder.title,
        content=reminder.description,
        channels=reminder.remind_channels,
        scheduled_time=scheduled_time,
        status=PushStatus.PENDING,
        retry_count=0,
        max_retries=3,
        priority=reminder.priority if hasattr(reminder, 'priority') else 1
    )
    
    db.add(push_task)
    await db.commit()
    await db.refresh(push_task)
    
    return push_task


async def generate_next_push_tasks(db: AsyncSession, reminder: Reminder, count: int = 1) -> list[PushTask]:
    """
    为周期性提醒生成接下来的N个推送任务
    
    Args:
        db: 数据库会话
        reminder: 提醒对象
        count: 生成任务数量
    
    Returns:
        生成的推送任务列表
    """
    if not reminder.is_active:
        return []
    
    tasks = []
    current_time = reminder.next_remind_time
    
    for _ in range(count):
        # 计算推送时间
        scheduled_time = current_time
        if reminder.advance_minutes > 0:
            scheduled_time = scheduled_time - timedelta(minutes=reminder.advance_minutes)
        
        # 创建推送任务
        push_task = PushTask(
            reminder_id=reminder.id,
            user_id=reminder.user_id,
            title=reminder.title,
            content=reminder.description,
            channels=reminder.remind_channels,
            scheduled_time=scheduled_time,
            status=PushStatus.PENDING,
            retry_count=0,
            max_retries=3,
            priority=reminder.priority if hasattr(reminder, 'priority') else 1
        )
        
        db.add(push_task)
        tasks.append(push_task)
        
        # 计算下次提醒时间
        current_time = calculate_next_occurrence(
            current_time,
            reminder.recurrence_type,
            reminder.recurrence_config
        )
    
    await db.commit()
    
    return tasks


async def update_push_task_status(
    db: AsyncSession, 
    task_id: int, 
    status: PushStatus,
    error_message: Optional[str] = None
) -> Optional[PushTask]:
    """
    更新推送任务状态
    
    Args:
        db: 数据库会话
        task_id: 任务ID
        status: 新状态
        error_message: 错误信息（如果有）
    
    Returns:
        更新后的推送任务对象
    """
    from sqlalchemy import select
    stmt = select(PushTask).where(PushTask.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    
    if not task:
        return None
    
    task.status = status
    
    if status == PushStatus.SENT:
        task.executed_at = datetime.now()
    elif status == PushStatus.FAILED:
        task.retry_count += 1
        if error_message:
            task.error_message = error_message
    
    await db.commit()
    await db.refresh(task)
    
    return task
