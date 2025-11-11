"""
Reminder Completion Model
提醒完成记录模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ReminderCompletion(Base):
    """Reminder completion table - 提醒完成记录表"""
    __tablename__ = "reminder_completions"
    
    id = Column(Integer, primary_key=True, index=True, comment="完成记录ID")
    reminder_id = Column(Integer, ForeignKey("reminders.id"), nullable=False, index=True, comment="提醒ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="完成用户ID")
    
    # Completion info (使用数据库现有字段名)
    scheduled_time = Column(DateTime(timezone=True), nullable=True, comment="计划时间")
    completed_time = Column(DateTime(timezone=True), nullable=False, index=True, comment="实际完成时间")
    status = Column(String(20), default="completed", comment="状态")
    delay_minutes = Column(Integer, default=0, comment="延迟分钟数")
    note = Column(String(500), nullable=True, comment="完成备注")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # Relationships
    reminder = relationship("Reminder", back_populates="completions")
    user = relationship("User", back_populates="reminder_completions")
