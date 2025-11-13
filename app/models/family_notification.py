"""
Family Notification Model
家庭通知模型 - 用于家庭成员之间的消息通知
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class NotificationType(str, enum.Enum):
    """通知类型"""
    REMINDER_COMPLETED = "reminder_completed"  # 提醒完成通知
    REMINDER_CREATED = "reminder_created"      # 新建提醒通知
    REMINDER_UPDATED = "reminder_updated"      # 提醒更新通知
    REMINDER_DELETED = "reminder_deleted"      # 提醒删除通知
    MEMBER_JOINED = "member_joined"            # 成员加入通知
    MEMBER_LEFT = "member_left"                # 成员离开通知


class FamilyNotification(Base):
    """家庭通知表"""
    __tablename__ = "family_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    family_group_id = Column(Integer, ForeignKey("family_groups.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 触发通知的用户
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # 接收通知的用户
    
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    
    # 关联对象信息
    related_reminder_id = Column(Integer, ForeignKey("reminders.id"), nullable=True)
    related_completion_id = Column(Integer, ForeignKey("reminder_completions.id"), nullable=True)
    
    # 元数据
    metadata_json = Column(Text, nullable=True)  # JSON格式的额外信息
    
    # 状态
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    family_group = relationship("FamilyGroup", backref="notifications")
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
    reminder = relationship("Reminder", backref="notifications")
    completion = relationship("ReminderCompletion", backref="notifications")
    
    def __repr__(self):
        return f"<FamilyNotification(id={self.id}, type={self.notification_type}, receiver={self.receiver_id})>"
