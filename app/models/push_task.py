"""
Push Task Model
推送任务模型
"""

from typing import List, Dict, Any, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, JSON, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.reminder import Reminder
    from app.models.user import User
    from app.models.push_log import PushLog


class PushStatus(str, enum.Enum):
    """推送状态枚举"""
    PENDING = "pending"    # 待推送
    SENT = "sent"          # 已发送
    FAILED = "failed"      # 发送失败
    CANCELLED = "cancelled"  # 已取消


class PushTask(Base):
    """Push task table - 推送任务表"""
    __tablename__ = "push_tasks"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="任务ID")
    reminder_id: Mapped[int] = mapped_column(ForeignKey("reminders.id"), index=True, comment="关联提醒ID")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment="用户ID")
    
    # Task info
    title: Mapped[str] = mapped_column(String(200), comment="推送标题")
    content: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="推送内容")
    channels: Mapped[List[str]] = mapped_column(type_=JSON, default=list, comment="推送渠道(JSON)")
    priority: Mapped[int] = mapped_column(default=1, comment="优先级: 1=普通, 2=重要, 3=紧急")
    
    # Scheduling
    scheduled_time: Mapped[datetime] = mapped_column(index=True, comment="计划推送时间")
    sent_time: Mapped[datetime | None] = mapped_column(nullable=True, comment="实际发送时间")
    
    # Status
    status: Mapped[PushStatus] = mapped_column(SQLEnum(PushStatus), default=PushStatus.PENDING, index=True, comment="推送状态")
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="错误信息")
    retry_count: Mapped[int] = mapped_column(default=0, comment="重试次数")
    max_retries: Mapped[int] = mapped_column(default=3, comment="最大重试次数")
    executed_at: Mapped[datetime | None] = mapped_column(nullable=True, comment="执行时间")
    
    # Response data
    push_response: Mapped[Dict[str, Any] | None] = mapped_column(type_=JSON, nullable=True, comment="推送服务响应(JSON)")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # Relationships
    reminder: Mapped["Reminder"] = relationship(back_populates="push_tasks")
    user: Mapped["User"] = relationship(back_populates="push_tasks")
    logs: Mapped[List["PushLog"]] = relationship(back_populates="task", cascade="all, delete-orphan")
