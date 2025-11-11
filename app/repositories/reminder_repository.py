"""
Reminder Repository - SQLAlchemy 2.0
提醒数据访问层
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.models.reminder import Reminder


class ReminderRepository:
    """提醒仓储类 - 使用SQLAlchemy 2.0语法"""
    
    @staticmethod
    def get_by_id(db: Session, reminder_id: int, user_id: int) -> Optional[Reminder]:
        """
        根据ID获取提醒（带用户权限检查）
        
        Args:
            db: 数据库会话
            reminder_id: 提醒ID
            user_id: 用户ID
            
        Returns:
            提醒或None
        """
        stmt = select(Reminder).where(
            and_(
                Reminder.id == reminder_id,
                Reminder.user_id == user_id
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    def list_by_user(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        is_active: Optional[bool] = None
    ) -> List[Reminder]:
        """
        获取用户的提醒列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过记录数
            limit: 返回记录数
            is_active: 是否活跃（可选筛选条件）
            
        Returns:
            提醒列表
        """
        # 构建查询条件
        conditions = [Reminder.user_id == user_id]
        if is_active is not None:
            conditions.append(Reminder.is_active == is_active)
        
        # 查询列表
        stmt = (
            select(Reminder)
            .where(and_(*conditions))
            .order_by(Reminder.next_remind_time)
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        reminders = result.scalars().all()
        
        return reminders
    
    @staticmethod
    def create(
        db: Session,
        user_id: int,
        title: str,
        description: Optional[str],
        category: str,
        recurrence_type: str,
        recurrence_config: Optional[dict],
        first_remind_time: datetime,
        remind_channels: List[str],
        advance_minutes: int,
        priority: int = 1,
        amount: Optional[int] = None,
        location: Optional[dict] = None,
        attachments: Optional[List[dict]] = None
    ) -> Reminder:
        """
        创建提醒
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            title: 标题
            description: 描述
            category: 分类
            recurrence_type: 重复类型
            recurrence_config: 重复配置
            first_remind_time: 首次提醒时间
            remind_channels: 提醒渠道
            advance_minutes: 提前分钟数
            priority: 优先级
            amount: 金额（以分为单位）
            location: 位置信息
            attachments: 附件列表
            
        Returns:
            创建的提醒
        """
        reminder = Reminder(
            user_id=user_id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            recurrence_type=recurrence_type,
            recurrence_config=recurrence_config,
            first_remind_time=first_remind_time,
            next_remind_time=first_remind_time,
            remind_channels=remind_channels,
            advance_minutes=advance_minutes,
            amount=amount,
            location=location,
            attachments=attachments
        )
        
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        
        return reminder
    
    @staticmethod
    def update(db: Session, reminder: Reminder, **kwargs) -> Reminder:
        """
        更新提醒
        
        Args:
            db: 数据库会话
            reminder: 提醒对象
            **kwargs: 要更新的字段
            
        Returns:
            更新后的提醒
        """
        for field, value in kwargs.items():
            if hasattr(reminder, field):
                setattr(reminder, field, value)
        
        db.commit()
        db.refresh(reminder)
        
        return reminder
    
    @staticmethod
    def delete(db: Session, reminder: Reminder) -> None:
        """
        删除提醒
        
        Args:
            db: 数据库会话
            reminder: 提醒对象
        """
        db.delete(reminder)
        db.commit()
