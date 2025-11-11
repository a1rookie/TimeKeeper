"""
Reminder Schemas
提醒相关的 Pydantic 模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.reminder import RecurrenceType, ReminderCategory


class ReminderBase(BaseModel):
    """Reminder base schema"""
    title: str = Field(..., max_length=100, description="提醒标题")
    description: Optional[str] = Field(None, max_length=500, description="提醒描述")
    category: ReminderCategory = Field(..., description="分类")
    recurrence_type: RecurrenceType = Field(..., description="周期类型")
    recurrence_config: dict = Field(default_factory=dict, description="周期配置")
    remind_channels: List[str] = Field(default=["app"], description="提醒渠道")
    advance_minutes: int = Field(default=0, ge=0, description="提前提醒分钟数")


class ReminderCreate(ReminderBase):
    """Reminder creation schema"""
    first_remind_time: datetime = Field(..., description="首次提醒时间")


class ReminderUpdate(BaseModel):
    """Reminder update schema"""
    title: Optional[str] = Field(None, max_length=100, description="提醒标题")
    description: Optional[str] = Field(None, max_length=500, description="提醒描述")
    category: Optional[ReminderCategory] = Field(None, description="分类")
    recurrence_type: Optional[RecurrenceType] = Field(None, description="周期类型")
    recurrence_config: Optional[dict] = Field(None, description="周期配置")
    remind_channels: Optional[List[str]] = Field(None, description="提醒渠道")
    advance_minutes: Optional[int] = Field(None, ge=0, description="提前提醒分钟数")
    is_active: Optional[bool] = Field(None, description="是否启用")


class ReminderResponse(ReminderBase):
    """Reminder response schema"""
    id: int
    user_id: int
    first_remind_time: datetime
    next_remind_time: datetime
    last_remind_time: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class VoiceReminderCreate(BaseModel):
    """Voice input reminder creation schema"""
    audio_base64: str = Field(..., description="Base64编码的音频数据")
    audio_format: str = Field(default="wav", description="音频格式")


class QuickReminderCreate(BaseModel):
    """Quick reminder creation from template"""
    template_id: str = Field(..., description="模板ID")
    custom_data: dict = Field(default_factory=dict, description="自定义数据")
