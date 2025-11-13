"""
Reminder Notification Model
提醒通知模型 - 高级提醒策略配置
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class ReminderNotification(Base):
    """提醒通知表 - 存储提醒的通知策略"""
    __tablename__ = "reminder_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    reminder_id = Column(Integer, ForeignKey("reminders.id"), nullable=False, unique=True, index=True)
    
    # ===== 提前通知配置 =====
    advance_notify_enabled = Column(Boolean, default=False, nullable=False, comment="是否启用提前通知")
    advance_days = Column(Integer, default=0, comment="提前几天开始通知（如生日提前5天）")
    advance_notify_interval = Column(Integer, default=1, comment="提前通知间隔天数（如每2天通知一次）")
    advance_notify_time = Column(String(5), default="09:00", comment="提前通知时间（HH:MM格式）")
    
    # ===== 当天通知配置 =====
    same_day_notifications = Column(JSON, nullable=True, comment="当天通知时间列表 ['08:00', '12:00', '20:00']")
    
    # ===== 智能时间调整 =====
    avoid_night_time = Column(Boolean, default=True, nullable=False, comment="避免夜间通知（22:00-07:00）")
    night_time_fallback = Column(String(5), default="09:00", comment="夜间时间回退到的时间")
    
    # ===== 其他配置 =====
    custom_message_template = Column(Text, nullable=True, comment="自定义通知消息模板")
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    reminder = relationship("Reminder", backref="notification_config")
    
    def __repr__(self):
        return f"<ReminderNotification(reminder_id={self.reminder_id}, advance_days={self.advance_days})>"
