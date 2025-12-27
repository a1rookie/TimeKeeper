"""
Reminder Schemas
提醒相关的 Pydantic 模型
"""

from pydantic import BaseModel, Field, field_validator
from typing import List
from datetime import datetime
from app.models.reminder import RecurrenceType, ReminderCategory


class ReminderBase(BaseModel):
    """Reminder base schema"""
    title: str = Field(..., max_length=200, description="提醒标题")
    description: str | None = Field(None, max_length=1000, description="提醒描述")
    category: ReminderCategory = Field(..., description="分类")
    priority: int = Field(default=1, ge=1, le=3, description="优先级: 1=普通, 2=重要, 3=紧急")
    recurrence_type: RecurrenceType = Field(default=RecurrenceType.ONCE, description="周期类型")
    recurrence_config: dict = Field(default_factory=dict, description="周期配置")
    remind_channels: List[str] = Field(default=["app"], description="提醒渠道: app, sms, wechat, call")
    advance_minutes: int = Field(default=0, ge=0, description="提前提醒分钟数")
    amount: int | None = Field(None, description="金额（分）")
    location: dict | None = Field(None, description="位置信息")
    attachments: List[dict] | None = Field(None, description="附件列表")
    
    @field_validator('remind_channels')
    @classmethod
    def validate_channels(cls, v: List[str]) -> List[str]:
        """验证提醒渠道"""
        valid_channels = {"app", "sms", "wechat", "call"}
        if not v:
            return ["app"]  # 默认使用 app 渠道
        
        invalid = [ch for ch in v if ch not in valid_channels]
        if invalid:
            raise ValueError(f"无效的提醒渠道: {invalid}，可选值: {valid_channels}")
        return v
    
    @field_validator('recurrence_config')
    @classmethod
    def validate_recurrence_config(cls, v: dict, info) -> dict:
        """验证周期配置"""
        if not v:
            return {}
        
        # 获取 recurrence_type（如果在验证上下文中）
        recurrence_type = info.data.get('recurrence_type')
        if not recurrence_type:
            return v
        
        # WEEKLY 需要指定星期几
        if recurrence_type == RecurrenceType.WEEKLY:
            if 'weekdays' not in v:
                raise ValueError("周周期提醒需要指定 'weekdays' 字段（1-7表示周一到周日）")
            weekdays = v['weekdays']
            if not isinstance(weekdays, list) or not weekdays:
                raise ValueError("'weekdays' 必须是非空数组")
            if not all(isinstance(d, int) and 1 <= d <= 7 for d in weekdays):
                raise ValueError("'weekdays' 的值必须在 1-7 之间")
        
        # MONTHLY 需要指定日期
        elif recurrence_type == RecurrenceType.MONTHLY:
            if 'days' not in v:
                raise ValueError("月周期提醒需要指定 'days' 字段（1-31表示每月的日期）")
            days = v['days']
            if not isinstance(days, list) or not days:
                raise ValueError("'days' 必须是非空数组")
            if not all(isinstance(d, int) and 1 <= d <= 31 for d in days):
                raise ValueError("'days' 的值必须在 1-31 之间")
        
        # YEARLY 需要指定月份和日期
        elif recurrence_type == RecurrenceType.YEARLY:
            if 'month' not in v or 'day' not in v:
                raise ValueError("年周期提醒需要指定 'month' 和 'day' 字段")
            month = v['month']
            day = v['day']
            if not isinstance(month, int) or not 1 <= month <= 12:
                raise ValueError("'month' 的值必须在 1-12 之间")
            if not isinstance(day, int) or not 1 <= day <= 31:
                raise ValueError("'day' 的值必须在 1-31 之间")
        
        # CUSTOM 需要指定间隔
        elif recurrence_type == RecurrenceType.CUSTOM:
            if 'interval' not in v or 'unit' not in v:
                raise ValueError("自定义周期提醒需要指定 'interval'（间隔数）和 'unit'（单位：days/weeks/months/years）")
            interval = v['interval']
            unit = v['unit']
            if not isinstance(interval, int) or interval <= 0:
                raise ValueError("'interval' 必须是正整数")
            if unit not in ['days', 'weeks', 'months', 'years']:
                raise ValueError("'unit' 必须是 'days', 'weeks', 'months' 或 'years'")
        
        return v


class ReminderCreate(ReminderBase):
    """Reminder creation schema"""
    first_remind_time: datetime = Field(..., description="首次提醒时间")


class ReminderUpdate(BaseModel):
    """Reminder update schema"""
    title: str | None = Field(None, max_length=200, description="提醒标题")
    description: str | None = Field(None, max_length=1000, description="提醒描述")
    category: ReminderCategory | None = Field(None, description="分类")
    priority: int | None = Field(None, ge=1, le=3, description="优先级")
    recurrence_type: RecurrenceType | None = Field(None, description="周期类型")
    recurrence_config: dict | None = Field(None, description="周期配置")
    remind_channels: List[str] | None = Field(None, description="提醒渠道")
    advance_minutes: int | None = Field(None, ge=0, description="提前提醒分钟数")
    amount: int | None = Field(None, description="金额（以分为单位）")
    location: dict | None = Field(None, description="位置信息")
    attachments: List[dict] | None = Field(None, description="附件列表")
    is_active: bool | None = Field(None, description="是否启用")
    is_completed: bool | None = Field(None, description="是否已完成")


class ReminderResponse(ReminderBase):
    """Reminder response schema"""
    id: int
    user_id: int
    first_remind_time: datetime
    next_remind_time: datetime
    last_remind_time: datetime | None = None
    is_active: bool
    is_completed: bool = False
    completed_at: datetime | None = None
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
