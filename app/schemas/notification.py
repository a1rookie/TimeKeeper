"""
Family Notification Schemas
家庭通知的 Pydantic 模型
"""
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.family_notification import NotificationType


class FamilyNotificationResponse(BaseModel):
    """通知响应"""
    id: int
    family_group_id: int
    sender_id: int
    receiver_id: int
    notification_type: NotificationType
    title: str
    content: str | None = None
    related_reminder_id: int | None = None
    related_completion_id: int | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class NotificationStats(BaseModel):
    """通知统计"""
    total_count: int = Field(description="总通知数")
    unread_count: int = Field(description="未读通知数")
