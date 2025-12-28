"""
Reminder Schemas
提醒相关的 Pydantic 模型
"""

from pydantic import BaseModel, Field, field_validator
from typing import List
from datetime import datetime
from app.models.reminder import RecurrenceType, ReminderCategory
from app.core.config import settings


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
    
    @field_validator('location')
    @classmethod
    def validate_location(cls, v: dict | None) -> dict | None:
        """验证位置信息格式（仅在有值时验证）"""
        if v is None:
            return None
        
        # 如果提供了经纬度，必须同时提供且在有效范围内
        has_lat = 'latitude' in v
        has_lng = 'longitude' in v
        
        if has_lat or has_lng:
            if not (has_lat and has_lng):
                raise ValueError("latitude 和 longitude 必须同时提供")
            
            lat = v['latitude']
            lng = v['longitude']
            
            if not isinstance(lat, (int, float)) or not -90 <= lat <= 90:
                raise ValueError("latitude 必须在 -90 到 90 之间")
            if not isinstance(lng, (int, float)) or not -180 <= lng <= 180:
                raise ValueError("longitude 必须在 -180 到 180 之间")
        
        # address 字段长度限制
        if 'address' in v:
            address = str(v['address'])
            if len(address) > 500:
                raise ValueError("address 长度不能超过 500 字符")
            if len(address.strip()) == 0:
                raise ValueError("address 不能为空字符串")
        
        return v
    
    @field_validator('attachments')
    @classmethod
    def validate_attachments(cls, v: List[dict] | None) -> List[dict] | None:
        """
        验证附件列表（仅在有值时验证）
        
        附件格式：
        [
            {
                "file_id": "uuid-string",           # 文件ID（上传后返回）
                "file_name": "合同.pdf",            # 文件名
                "file_size": 1024000,               # 文件大小（字节）
                "file_type": "application/pdf",     # MIME类型
                "file_url": "https://..."           # 访问URL
            }
        ]
        
        工作流程：
        1. 前端先调用文件上传接口 POST /api/v1/attachments/upload
        2. 后端保存文件并返回 file_id 和 file_url
        3. 创建提醒时将文件信息传入 attachments 字段
        """
        if v is None:
            return None
        
        if not isinstance(v, list):
            raise ValueError("attachments 必须是数组")
        
        if len(v) == 0:
            return None  # 空数组等同于 None
        
        # 限制附件数量
        if len(v) > settings.MAX_ATTACHMENTS_PER_REMINDER:
            raise ValueError(f"附件数量不能超过 {settings.MAX_ATTACHMENTS_PER_REMINDER} 个")
        
        # 验证每个附件的格式
        for idx, attachment in enumerate(v):
            if not isinstance(attachment, dict):
                raise ValueError(f"附件 {idx} 格式错误，必须是对象")
            
            # file_id 是必需的（上传后获得）
            if 'file_id' not in attachment:
                raise ValueError(f"附件 {idx} 缺少 file_id 字段（请先上传文件）")
            
            # file_url 是必需的
            if 'file_url' not in attachment:
                raise ValueError(f"附件 {idx} 缺少 file_url 字段")
            
            # 文件名验证
            if 'file_name' in attachment:
                name = str(attachment['file_name'])
                if len(name) > 255:
                    raise ValueError(f"附件 {idx} 的文件名长度不能超过 255 字符")
                if len(name.strip()) == 0:
                    raise ValueError(f"附件 {idx} 的文件名不能为空")
            
            # 文件大小验证
            if 'file_size' in attachment:
                size = attachment['file_size']
                if not isinstance(size, int) or size <= 0:
                    raise ValueError(f"附件 {idx} 的 file_size 必须是正整数")
                if size > settings.MAX_ATTACHMENT_SIZE:
                    max_mb = settings.MAX_ATTACHMENT_SIZE // (1024 * 1024)
                    raise ValueError(f"附件 {idx} 的文件大小不能超过 {max_mb}MB")
        
        return v


class ReminderCreate(ReminderBase):
    """Reminder creation schema"""
    first_remind_time: datetime = Field(..., description="首次提醒时间")


class ReminderUpdate(ReminderBase):
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
    
    @field_validator('remind_channels')
    @classmethod
    def validate_channels(cls, v: List[str] | None) -> List[str] | None:
        """验证提醒渠道"""
        if v is None:
            return None
        valid_channels = {"app", "sms", "wechat", "call"}
        if not v:
            return ["app"]  # 默认使用 app 渠道
        invalid = [ch for ch in v if ch not in valid_channels]
        if invalid:
            raise ValueError(f"无效的提醒渠道: {invalid}，可选值: {valid_channels}")
        return v
    
    @field_validator('recurrence_config')
    @classmethod
    def validate_recurrence_config(cls, v: dict | None, info) -> dict | None:
        """验证周期配置"""
        if v is None or not v:
            return v
        
        # 获取 recurrence_type（如果在验证上下文中）
        recurrence_type = info.data.get('recurrence_type')
        if not recurrence_type:
            return v
        
        # 复用 ReminderBase 的验证逻辑
        if recurrence_type == RecurrenceType.WEEKLY:
            if 'weekdays' not in v:
                raise ValueError("周周期提醒需要指定 'weekdays' 字段（1-7表示周一到周日）")
            weekdays = v['weekdays']
            if not isinstance(weekdays, list) or not weekdays:
                raise ValueError("'weekdays' 必须是非空数组")
            if not all(isinstance(d, int) and 1 <= d <= 7 for d in weekdays):
                raise ValueError("'weekdays' 的值必须在 1-7 之间")
        elif recurrence_type == RecurrenceType.MONTHLY:
            if 'days' not in v:
                raise ValueError("月周期提醒需要指定 'days' 字段（1-31表示每月的日期）")
            days = v['days']
            if not isinstance(days, list) or not days:
                raise ValueError("'days' 必须是非空数组")
            if not all(isinstance(d, int) and 1 <= d <= 31 for d in days):
                raise ValueError("'days' 的值必须在 1-31 之间")
        elif recurrence_type == RecurrenceType.YEARLY:
            if 'month' not in v or 'day' not in v:
                raise ValueError("年周期提醒需要指定 'month' 和 'day' 字段")
            month = v['month']
            day = v['day']
            if not isinstance(month, int) or not 1 <= month <= 12:
                raise ValueError("'month' 的值必须在 1-12 之间")
            if not isinstance(day, int) or not 1 <= day <= 31:
                raise ValueError("'day' 的值必须在 1-31 之间")
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
    
    @field_validator('location')
    @classmethod
    def validate_location(cls, v: dict | None) -> dict | None:
        """验证位置信息格式（仅在有值时验证）"""
        if v is None:
            return None
        has_lat = 'latitude' in v
        has_lng = 'longitude' in v
        if has_lat or has_lng:
            if not (has_lat and has_lng):
                raise ValueError("latitude 和 longitude 必须同时提供")
            lat = v['latitude']
            lng = v['longitude']
            if not isinstance(lat, (int, float)) or not -90 <= lat <= 90:
                raise ValueError("latitude 必须在 -90 到 90 之间")
            if not isinstance(lng, (int, float)) or not -180 <= lng <= 180:
                raise ValueError("longitude 必须在 -180 到 180 之间")
        if 'address' in v:
            address = str(v['address'])
            if len(address) > 500:
                raise ValueError("address 长度不能超过 500 字符")
            if len(address.strip()) == 0:
                raise ValueError("address 不能为空字符串")
        return v
    
    @field_validator('attachments')
    @classmethod
    def validate_attachments(cls, v: List[dict] | None) -> List[dict] | None:
        """验证附件列表（仅在有值时验证）"""
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError("attachments 必须是数组")
        if len(v) == 0:
            return None
        if len(v) > settings.MAX_ATTACHMENTS_PER_REMINDER:
            raise ValueError(f"附件数量不能超过 {settings.MAX_ATTACHMENTS_PER_REMINDER} 个")
        for idx, attachment in enumerate(v):
            if not isinstance(attachment, dict):
                raise ValueError(f"附件 {idx} 格式错误，必须是对象")
            if 'file_id' not in attachment:
                raise ValueError(f"附件 {idx} 缺少 file_id 字段（请先上传文件）")
            if 'file_url' not in attachment:
                raise ValueError(f"附件 {idx} 缺少 file_url 字段")
            if 'file_name' in attachment:
                name = str(attachment['file_name'])
                if len(name) > 255:
                    raise ValueError(f"附件 {idx} 的文件名长度不能超过 255 字符")
                if len(name.strip()) == 0:
                    raise ValueError(f"附件 {idx} 的文件名不能为空")
            if 'file_size' in attachment:
                size = attachment['file_size']
                if not isinstance(size, int) or size <= 0:
                    raise ValueError(f"附件 {idx} 的 file_size 必须是正整数")
                if size > settings.MAX_ATTACHMENT_SIZE:
                    max_mb = settings.MAX_ATTACHMENT_SIZE // (1024 * 1024)
                    raise ValueError(f"附件 {idx} 的文件大小不能超过 {max_mb}MB")
        return v


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
