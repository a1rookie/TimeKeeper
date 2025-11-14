"""
Reminder Notification Model
提醒通知模型 - 高级提醒策略配置
"""
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Text, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.reminder import Reminder


class ReminderNotification(Base):
    """提醒通知表 - 存储提醒的通知策略"""
    __tablename__ = "reminder_notifications"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    reminder_id: Mapped[int] = mapped_column(ForeignKey("reminders.id"), unique=True, index=True)
    
    # ===== 提前通知配置 =====
    advance_notify_enabled: Mapped[bool] = mapped_column(default=False, comment="是否启用提前通知")
    advance_days: Mapped[int] = mapped_column(default=0, comment="提前几天开始通知（如生日提前5天）")
    advance_notify_interval: Mapped[int] = mapped_column(default=1, comment="提前通知间隔天数（如每2天通知一次）")
    advance_notify_time: Mapped[str] = mapped_column(String(5), default="09:00", comment="提前通知时间（HH:MM格式）")
    
    # ===== 当天通知配置 =====
    same_day_notifications: Mapped[Optional[List[str]]] = mapped_column(type_=JSON, nullable=True, comment="当天通知时间列表 ['08:00', '12:00', '20:00']")
    
    # ===== 智能时间调整 =====
    avoid_night_time: Mapped[bool] = mapped_column(default=True, comment="避免夜间通知（22:00-07:00）")
    night_time_fallback: Mapped[str] = mapped_column(String(5), default="09:00", comment="夜间时间回退到的时间")
    
    # ===== 其他配置 =====
    custom_message_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="自定义通知消息模板")
    is_active: Mapped[bool] = mapped_column(default=True)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    
    # 关系
    reminder: Mapped["Reminder"] = relationship(backref="notification_config")
    
    def __repr__(self):
        return f"<ReminderNotification(reminder_id={self.reminder_id}, advance_days={self.advance_days})>"
