"""
Push Log Model
推送日志模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class PushLog(Base):
    """推送详细日志表"""
    __tablename__ = "push_logs"
    
    id = Column(Integer, primary_key=True, index=True, comment="日志ID")
    task_id = Column(Integer, ForeignKey("push_tasks.id"), comment="推送任务ID")
    reminder_id = Column(Integer, ForeignKey("reminders.id"), index=True, comment="提醒ID")
    user_id = Column(Integer, ForeignKey("users.id"), comment="用户ID")
    push_time = Column(DateTime(timezone=True), server_default=func.now(), index=True, comment="推送时间")
    channel = Column(String(20), nullable=False, comment="推送渠道: app, sms, wechat, call")
    status = Column(String(20), nullable=False, comment="推送状态: success, failed")
    error_message = Column(Text, comment="错误信息")
    user_action = Column(String(20), comment="用户操作: confirmed, ignored, delayed, dismissed")
    user_action_time = Column(DateTime(timezone=True), comment="用户操作时间")
    response_time_seconds = Column(Integer, comment="响应时间(秒)")
    
    # Relationships
    task = relationship("PushTask", back_populates="logs")
    reminder = relationship("Reminder")
    user = relationship("User", back_populates="push_logs")
