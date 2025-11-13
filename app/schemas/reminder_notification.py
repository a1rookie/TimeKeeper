"""
Reminder Notification Schemas
提醒通知策略的 Pydantic 模型
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class ReminderNotificationCreate(BaseModel):
    """创建通知策略"""
    # 提前通知配置
    advance_notify_enabled: bool = Field(False, description="是否启用提前通知")
    advance_days: int = Field(0, ge=0, le=365, description="提前几天开始通知（0-365天）")
    advance_notify_interval: int = Field(1, ge=1, le=30, description="提前通知间隔天数（1-30天）")
    advance_notify_time: str = Field("09:00", description="提前通知时间（HH:MM格式）")
    
    # 当天通知配置
    same_day_notifications: Optional[List[str]] = Field(None, description="当天通知时间列表 ['08:00', '12:00', '20:00']")
    
    # 智能时间调整
    avoid_night_time: bool = Field(True, description="避免夜间通知（22:00-07:00）")
    night_time_fallback: str = Field("09:00", description="夜间时间回退到的时间")
    
    # 其他
    custom_message_template: Optional[str] = Field(None, description="自定义通知消息模板")
    
    @validator('advance_notify_time', 'night_time_fallback')
    def validate_time_format(cls, v):
        """验证时间格式"""
        try:
            hour, minute = map(int, v.split(':'))
            if not (0 <= hour < 24 and 0 <= minute < 60):
                raise ValueError("时间必须在 00:00-23:59 范围内")
            return v
        except (ValueError, AttributeError):
            raise ValueError("时间格式必须为 HH:MM")
    
    @validator('same_day_notifications')
    def validate_same_day_times(cls, v):
        """验证当天通知时间列表"""
        if v is None:
            return v
        
        for time_str in v:
            try:
                hour, minute = map(int, time_str.split(':'))
                if not (0 <= hour < 24 and 0 <= minute < 60):
                    raise ValueError(f"时间 {time_str} 必须在 00:00-23:59 范围内")
            except (ValueError, AttributeError):
                raise ValueError(f"时间格式必须为 HH:MM，错误值: {time_str}")
        
        return v


class ReminderNotificationUpdate(BaseModel):
    """更新通知策略"""
    advance_notify_enabled: Optional[bool] = None
    advance_days: Optional[int] = Field(None, ge=0, le=365)
    advance_notify_interval: Optional[int] = Field(None, ge=1, le=30)
    advance_notify_time: Optional[str] = None
    same_day_notifications: Optional[List[str]] = None
    avoid_night_time: Optional[bool] = None
    night_time_fallback: Optional[str] = None
    custom_message_template: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('advance_notify_time', 'night_time_fallback')
    def validate_time_format(cls, v):
        """验证时间格式"""
        if v is None:
            return v
        try:
            hour, minute = map(int, v.split(':'))
            if not (0 <= hour < 24 and 0 <= minute < 60):
                raise ValueError("时间必须在 00:00-23:59 范围内")
            return v
        except (ValueError, AttributeError):
            raise ValueError("时间格式必须为 HH:MM")


class ReminderNotificationResponse(BaseModel):
    """通知策略响应"""
    id: int
    reminder_id: int
    advance_notify_enabled: bool
    advance_days: int
    advance_notify_interval: int
    advance_notify_time: str
    same_day_notifications: Optional[List[str]] = None
    avoid_night_time: bool
    night_time_fallback: str
    custom_message_template: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class NotificationScheduleResponse(BaseModel):
    """通知时间表响应"""
    reminder_id: int
    reminder_title: str
    reminder_time: datetime
    notification_times: List[datetime] = Field(description="所有通知时间列表（已排序）")
    advance_notifications: List[datetime] = Field(description="提前通知时间列表")
    same_day_notifications: List[datetime] = Field(description="当天通知时间列表")
    total_count: int = Field(description="总通知次数")
