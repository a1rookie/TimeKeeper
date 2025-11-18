"""
Push Scheduler - 推送任务调度器
负责扫描待推送任务并执行推送
"""

import asyncio
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models.push_task import PushStatus
from app.models.reminder import Reminder
from app.repositories.push_task_repository import PushTaskRepository
from app.services.jpush_service import push_reminder_notification
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)


class PushScheduler:
    """
    推送任务调度器
    """
    
    def __init__(self, interval: int = 60):
        """
        初始化调度器
        
        Args:
            interval: 扫描间隔（秒）
        """
        self.interval = interval
        self.running = False
    
    async def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("Push scheduler is already running")
            return
        
        self.running = True
        logger.info("Push scheduler started")
        
        while self.running:
            try:
                await self._scan_and_push()
            except Exception as e:
                logger.error(f"Error in push scheduler: {e}", exc_info=True)
            
            # 等待下一次扫描
            await asyncio.sleep(self.interval)
    
    async def stop(self):
        """停止调度器"""
        self.running = False
        logger.info("Push scheduler stopped")
    
    async def _scan_and_push(self):
        """扫描并推送待发送任务"""
        async with async_session_maker() as db:
            try:
                # 查找需要推送的任务
                now = datetime.now()
                pending_tasks = await PushTaskRepository.get_pending_tasks_static(
                    db=db,
                    before_time=now
                )
                
                if not pending_tasks:
                    logger.debug("No pending push tasks found")
                    return
                
                logger.info(f"Found {len(pending_tasks)} pending push tasks")
                
                # 执行推送
                for task in pending_tasks:
                    await self._execute_push_task(db, task)
                
                await db.commit()
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error scanning push tasks: {e}", exc_info=True)
    
    async def _execute_push_task(self, db: AsyncSession, task):
        """
        执行单个推送任务
        
        Args:
            db: 数据库会话
            task: 推送任务对象
        """
        repo = PushTaskRepository(db)
        try:
            logger.info(f"Executing push task {task.id} for user {task.user_id}")
            
            # 检查推送是否启用
            if not settings.JPUSH_ENABLED:
                logger.warning(f"JPush disabled, skipping task {task.id}")
                await repo.update_status(
                    task=task,
                    status=PushStatus.CANCELLED,
                    error_message="JPush is disabled"
                )
                return
            
            # 执行推送
            result = push_reminder_notification(
                user_id=task.user_id,
                reminder_id=task.reminder_id,
                title=task.title,
                content=task.content or ""
            )
            
            # 更新任务状态
            if result.get("success"):
                await repo.update_status(task=task, status=PushStatus.SENT, push_response=result)
                logger.info(f"Push task {task.id} sent successfully")
            else:
                # 推送失败，检查是否需要重试
                if task.retry_count >= 2:  # 已经重试2次，总共3次
                    await repo.update_status(
                        task=task,
                        status=PushStatus.FAILED,
                        error_message=result.get("error", "Unknown error")
                    )
                    logger.error(f"Push task {task.id} failed after {task.retry_count + 1} attempts")
                else:
                    # 延迟重试（保持PENDING状态，更新scheduled_time）
                    retry_minutes = 5 * (task.retry_count + 1)
                    task.scheduled_time = datetime.now() + timedelta(minutes=retry_minutes)
                    task.error_message = f"Retry {task.retry_count + 1}: {result.get('error', 'Unknown error')}"
                    task.push_response = result
                    task.retry_count += 1
                    await db.commit()
                    await db.refresh(task)
                    logger.warning(f"Push task {task.id} failed, will retry in {retry_minutes} minutes")
        
        except Exception as e:
            logger.error(f"Error executing push task {task.id}: {e}", exc_info=True)
            
            if task.retry_count >= 2:
                await repo.update_status(task=task, status=PushStatus.FAILED, error_message=str(e))
            else:
                retry_minutes = 5 * (task.retry_count + 1)
                task.scheduled_time = datetime.now() + timedelta(minutes=retry_minutes)
                task.error_message = f"Exception retry {task.retry_count + 1}: {str(e)}"
                task.retry_count += 1
                await db.commit()
                await db.refresh(task)


async def create_push_task_for_reminder(
    db: AsyncSession,
    reminder_id: int,
    user_id: int,
    scheduled_time: datetime
):
    """
    为提醒创建推送任务
    
    Args:
        db: 数据库会话
        reminder_id: 提醒ID
        user_id: 用户ID
        scheduled_time: 计划推送时间
        
    Returns:
        创建的推送任务
    """
    # 获取提醒信息（使用SQLAlchemy 2.0语法）
    from sqlalchemy import select
    stmt = select(Reminder).where(Reminder.id == reminder_id)
    result = await db.execute(stmt)
    reminder = result.scalar_one_or_none()
    
    if not reminder:
        raise ValueError(f"Reminder {reminder_id} not found")
    
    # 使用Repository创建推送任务
    repo = PushTaskRepository(db)
    push_task = await repo.create(
        user_id=user_id,
        reminder_id=reminder_id,
        title=reminder.title,
        content=reminder.description or f"提醒：{reminder.title}",
        channels=reminder.remind_channels,
        scheduled_time=scheduled_time
    )
    
    logger.info(f"Created push task {push_task.id} for reminder {reminder_id}")
    
    return push_task


async def batch_create_push_tasks(
    db: AsyncSession,
    tasks_data: List[dict]
) -> List:
    """
    批量创建推送任务
    
    Args:
        db: 数据库会话
        tasks_data: 任务数据列表，每项包含 reminder_id, user_id, scheduled_time
        
    Returns:
        创建的推送任务列表
    """
    push_tasks = []
    
    for data in tasks_data:
        try:
            task = await create_push_task_for_reminder(
                db=db,
                reminder_id=data["reminder_id"],
                user_id=data["user_id"],
                scheduled_time=data["scheduled_time"]
            )
            push_tasks.append(task)
        except Exception as e:
            logger.error(f"Failed to create push task: {e}")
    
    return push_tasks


# 全局调度器实例
_scheduler: PushScheduler | None = None


def get_scheduler() -> PushScheduler:
    """获取调度器单例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = PushScheduler()
    return _scheduler
