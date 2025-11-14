"""
Family Notification Model
家庭通知模型 - 用于家庭成员之间的消息通知
"""
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Text, Boolean, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.family_group import FamilyGroup
    from app.models.user import User
    from app.models.reminder import Reminder
    from app.models.reminder_completion import ReminderCompletion


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
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    family_group_id: Mapped[int] = mapped_column(ForeignKey("family_groups.id"), index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # 触发通知的用户
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)  # 接收通知的用户
    
    notification_type: Mapped[NotificationType] = mapped_column(SQLEnum(NotificationType))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 关联对象信息
    related_reminder_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reminders.id"), nullable=True)
    related_completion_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reminder_completions.id"), nullable=True)
    
    # 元数据
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON格式的额外信息
    
    # 状态
    is_read: Mapped[bool] = mapped_column(default=False, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    # 关系
    family_group: Mapped["FamilyGroup"] = relationship(backref="notifications")
    sender: Mapped["User"] = relationship(foreign_keys=[sender_id])
    receiver: Mapped["User"] = relationship(foreign_keys=[receiver_id])
    reminder = relationship("Reminder", backref="notifications")
    completion = relationship("ReminderCompletion", backref="notifications")
    
    def __repr__(self):
        return f"<FamilyNotification(id={self.id}, type={self.notification_type}, receiver={self.receiver_id})>"
