"""
PushLog Model
推送详细日志模型
"""

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class PushLog(Base):
    """PushLog table - 推送详细日志表"""
    __tablename__ = "push_logs"
    
    id = Column(BigInteger, primary_key=True, index=True, comment="日志ID")
    task_id = Column(BigInteger, ForeignKey("push_tasks.id"), nullable=True, comment="推送任务ID")
    reminder_id = Column(BigInteger, ForeignKey("reminders.id"), nullable=False, index=True, comment="提醒ID")
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, comment="用户ID")
    push_time = Column(DateTime(timezone=True), server_default=func.now(), index=True, comment="推送时间")
    channel = Column(String(20), nullable=False, comment="推送渠道: app, sms, wechat, call")
    status = Column(String(20), nullable=False, comment="状态: success, failed")
    error_message = Column(Text, nullable=True, comment="错误信息")
    user_action = Column(String(20), nullable=True, comment="用户操作: confirmed, ignored, delayed, dismissed")
    user_action_time = Column(DateTime(timezone=True), nullable=True, comment="用户操作时间")
    response_time_seconds = Column(Integer, nullable=True, comment="响应时间(秒)")
    
    # Relationships
    task = relationship("PushTask", back_populates="logs")
    reminder = relationship("Reminder", back_populates="push_logs")
    user = relationship("User", back_populates="push_logs")
