"""
Reminder Completion Schemas
提醒完成记录的数据模型
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ReminderCompletionBase(BaseModel):
    """完成记录基础模型"""
    note: str | None = None


class ReminderCompletionCreate(ReminderCompletionBase):
    """创建完成记录"""
    scheduled_time: datetime | None = None
    status: str = "completed"


class ReminderCompletionResponse(ReminderCompletionBase):
    """完成记录响应"""
    id: int
    reminder_id: int
    user_id: int
    scheduled_time: datetime | None
    completed_time: datetime
    status: str
    delay_minutes: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
