"""
Push Task Model
推送任务模型
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class PushStatus(str, enum.Enum):
    """推送状态枚举"""
    PENDING = "pending"    # 待推送
    SENT = "sent"          # 已发送
    FAILED = "failed"      # 发送失败
    CANCELLED = "cancelled"  # 已取消


class PushTask(Base):
    """Push task table - 推送任务表"""
    __tablename__ = "push_tasks"
    
    id = Column(Integer, primary_key=True, index=True, comment="任务ID")
    reminder_id = Column(Integer, ForeignKey("reminders.id"), nullable=False, index=True, comment="关联提醒ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    
    # Task info
    title = Column(String(100), nullable=False, comment="推送标题")
    content = Column(String(500), nullable=True, comment="推送内容")
    channels = Column(JSON, default=["app"], comment="推送渠道(JSON)")
    
    # Scheduling
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True, comment="计划推送时间")
    sent_time = Column(DateTime(timezone=True), nullable=True, comment="实际发送时间")
    
    # Status
    status = Column(SQLEnum(PushStatus), default=PushStatus.PENDING, index=True, comment="推送状态")
    error_message = Column(String(500), nullable=True, comment="错误信息")
    retry_count = Column(Integer, default=0, comment="重试次数")
    max_retries = Column(Integer, default=3, comment="最大重试次数")
    priority = Column(Integer, default=1, comment="优先级")
    executed_at = Column(DateTime(timezone=True), nullable=True, comment="执行时间")
    
    # Response data
    push_response = Column(JSON, nullable=True, comment="推送服务响应(JSON)")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # Relationships
    reminder = relationship("Reminder", back_populates="push_tasks")
    user = relationship("User", back_populates="push_tasks")
    logs = relationship("PushLog", back_populates="task", cascade="all, delete-orphan")
