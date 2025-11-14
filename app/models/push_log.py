"""
Push Log Model
推送日志模型
"""
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.push_task import PushTask
    from app.models.reminder import Reminder
    from app.models.user import User


class PushLog(Base):
    """推送详细日志表"""
    __tablename__ = "push_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="日志ID")
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("push_tasks.id"), nullable=True, comment="推送任务ID")
    reminder_id: Mapped[int] = mapped_column(ForeignKey("reminders.id"), index=True, comment="提醒ID")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), comment="用户ID")
    push_time: Mapped[datetime] = mapped_column(server_default=func.now(), index=True, comment="推送时间")
    channel: Mapped[str] = mapped_column(String(20), comment="推送渠道: app, sms, wechat, call")
    status: Mapped[str] = mapped_column(String(20), comment="推送状态: success, failed")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="错误信息")
    user_action: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="用户操作: confirmed, ignored, delayed, dismissed")
    user_action_time: Mapped[Optional[datetime]] = mapped_column(nullable=True, comment="用户操作时间")
    response_time_seconds: Mapped[Optional[int]] = mapped_column(nullable=True, comment="响应时间(秒)")
    
    # Relationships
    task: Mapped[Optional["PushTask"]] = relationship(back_populates="logs")
    reminder: Mapped["Reminder"] = relationship()
    user: Mapped["User"] = relationship(back_populates="push_logs")
