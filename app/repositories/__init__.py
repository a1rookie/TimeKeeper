"""
Repository Dependencies
数据仓库依赖注入
"""

from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.push_task_repository import PushTaskRepository
from app.repositories.reminder_completion_repository import ReminderCompletionRepository


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """获取用户仓库"""
    return UserRepository(db)


def get_reminder_repository(db: Session = Depends(get_db)) -> ReminderRepository:
    """获取提醒仓库"""
    return ReminderRepository(db)


def get_push_task_repository(db: Session = Depends(get_db)) -> PushTaskRepository:
    """获取推送任务仓库"""
    return PushTaskRepository(db)


def get_reminder_completion_repository(db: Session = Depends(get_db)) -> ReminderCompletionRepository:
    """获取提醒完成记录仓库"""
    return ReminderCompletionRepository(db)
