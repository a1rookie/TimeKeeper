"""
Repository Dependencies
数据仓库依赖注入 - 异步版本
"""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.push_task_repository import PushTaskRepository
from app.repositories.reminder_completion_repository import ReminderCompletionRepository


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[UserRepository, None]:
    """获取用户仓库"""
    yield UserRepository(db)


async def get_reminder_repository(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[ReminderRepository, None]:
    """获取提醒仓库"""
    yield ReminderRepository(db)


async def get_push_task_repository(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[PushTaskRepository, None]:
    """获取推送任务仓库"""
    yield PushTaskRepository(db)


async def get_reminder_completion_repository(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[ReminderCompletionRepository, None]:
    """获取提醒完成记录仓库"""
    yield ReminderCompletionRepository(db)
