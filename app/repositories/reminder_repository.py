"""
Reminder Repository
提醒数据访问层
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from app.models.reminder import Reminder, ReminderCategory, RecurrenceType


class ReminderRepository:
    """提醒数据仓库"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, reminder_id: int, user_id: int) -> Optional[Reminder]:
        """根据ID获取提醒（验证所有权）"""
        return self.db.query(Reminder).filter(
            and_(
                Reminder.id == reminder_id,
                Reminder.user_id == user_id
            )
        ).first()
    
    def get_user_reminders(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None,
        category: Optional[ReminderCategory] = None
    ) -> List[Reminder]:
        """获取用户的提醒列表"""
        query = self.db.query(Reminder).filter(Reminder.user_id == user_id)
        
        if is_active is not None:
            query = query.filter(Reminder.is_active == is_active)
        
        if category is not None:
            query = query.filter(Reminder.category == category)
        
        return query.order_by(Reminder.next_remind_time).offset(skip).limit(limit).all()
    
    def create(
        self,
        user_id: int,
        title: str,
        category: ReminderCategory,
        recurrence_type: RecurrenceType,
        first_remind_time: datetime,
        description: Optional[str] = None,
        recurrence_config: dict = None,
        remind_channels: List[str] = None,
        advance_minutes: int = 0,
        priority: int = 1,
        amount: Optional[int] = None,
        location: Optional[dict] = None,
        attachments: Optional[list] = None
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
        self.db.commit()
        self.db.refresh(new_reminder)
        return new_reminder
    
    def update(self, reminder: Reminder, **kwargs) -> Reminder:
        """更新提醒"""
        for field, value in kwargs.items():
            if hasattr(reminder, field) and value is not None:
                setattr(reminder, field, value)
        
        self.db.commit()
        self.db.refresh(reminder)
        return reminder
    
    def delete(self, reminder: Reminder) -> None:
        """删除提醒"""
        self.db.delete(reminder)
        self.db.commit()
    
    def mark_completed(self, reminder: Reminder, user_id: int) -> Reminder:
        """标记提醒为已完成，并返回更新后的提醒"""
        reminder.is_completed = True
        reminder.completed_at = datetime.now()
        self.db.commit()
        self.db.refresh(reminder)
        return reminder
    
    def mark_uncompleted(self, reminder: Reminder) -> Reminder:
        """取消完成状态"""
        reminder.is_completed = False
        reminder.completed_at = None
        self.db.commit()
        self.db.refresh(reminder)
        return reminder
    
    def update_next_remind_time(self, reminder: Reminder, next_time: datetime) -> Reminder:
        """更新下次提醒时间"""
        reminder.next_remind_time = next_time
        reminder.last_remind_time = reminder.completed_at or datetime.now()
        self.db.commit()
        self.db.refresh(reminder)
        return reminder
    
    def get_pending_reminders(self, before_time: datetime) -> List[Reminder]:
        """获取待推送的提醒（下次提醒时间在指定时间之前且未完成）"""
        return self.db.query(Reminder).filter(
            and_(
                Reminder.is_active == True,
                Reminder.is_completed == False,
                Reminder.next_remind_time <= before_time
            )
        ).all()
    
    def count_user_reminders(self, user_id: int, is_active: Optional[bool] = None) -> int:
        """统计用户提醒数量"""
        query = self.db.query(Reminder).filter(Reminder.user_id == user_id)
        
        if is_active is not None:
            query = query.filter(Reminder.is_active == is_active)
        
        return query.count()
