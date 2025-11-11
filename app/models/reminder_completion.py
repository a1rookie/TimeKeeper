"""
ReminderCompletion Model
提醒完成记录模型
"""

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ReminderCompletion(Base):
    """ReminderCompletion table - 提醒完成记录表"""
    __tablename__ = "reminder_completions"
    
    id = Column(BigInteger, primary_key=True, index=True, comment="记录ID")
    reminder_id = Column(BigInteger, ForeignKey("reminders.id"), nullable=False, index=True, comment="提醒ID")
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, comment="用户ID")
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True, comment="计划时间")
    completed_time = Column(DateTime(timezone=True), nullable=False, comment="完成时间")
    status = Column(String(20), default="completed", comment="状态: completed, delayed, skipped")
    delay_minutes = Column(Integer, nullable=True, comment="延迟分钟数")
    note = Column(Text, nullable=True, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # Relationships
    reminder = relationship("Reminder", back_populates="completions")
    user = relationship("User", back_populates="reminder_completions")
