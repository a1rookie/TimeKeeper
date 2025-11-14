"""
Reminder Completion Model
提醒完成记录模型
"""
import enum
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.reminder import Reminder
    from app.models.user import User


class CompletionStatus(str, enum.Enum):
    """完成状态枚举"""
    COMPLETED = "completed"
    DELAYED = "delayed"
    SKIPPED = "skipped"
    MISSED = "missed"


class ReminderCompletion(Base):
    """Reminder completion table - 提醒完成记录表"""
    __tablename__ = "reminder_completions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="完成记录ID")
    reminder_id: Mapped[int] = mapped_column(ForeignKey("reminders.id"), index=True, comment="提醒ID")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment="完成用户ID")
    
    # Completion info (使用数据库现有字段名)
    scheduled_time: Mapped[Optional[datetime]] = mapped_column(nullable=True, comment="计划时间")
    completed_time: Mapped[datetime] = mapped_column(index=True, comment="实际完成时间")
    status: Mapped[CompletionStatus] = mapped_column(Enum(CompletionStatus), default=CompletionStatus.COMPLETED, comment="状态")
    delay_minutes: Mapped[int] = mapped_column(default=0, comment="延迟分钟数")
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="完成备注")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), comment="创建时间")
    
    # Relationships
    reminder: Mapped["Reminder"] = relationship(back_populates="completions")
    user: Mapped["User"] = relationship(back_populates="reminder_completions")
