"""
Reminder Schemas
提醒相关的 Pydantic 模型
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List
from datetime import datetime, timezone
import enum
from app.models.reminder import RecurrenceType, RECOMMENDED_CATEGORIES
from app.core.config import settings


class ReminderBase(BaseModel):
    """Reminder base schema - 提醒基础字段"""
    
    model_config = ConfigDict(
        use_enum_values=True,  # 使用枚举的值而不是名称
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    # ========== 基本信息 ==========
    title: str = Field(
        ..., 
        max_length=200, 
        description="提醒标题（必填，最多200字）- 例如：'交房租'、'吃药提醒'"
    )
    description: str | None = Field(
        None, 
        max_length=1000, 
        description="提醒详细描述（可选，最多1000字）- 用于补充说明提醒内容"
    )
    
    # ========== 分类与优先级 ==========
    category: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="""提醒分类（必填，支持自定义）- 
推荐分类：rent(居住), health(健康), pet(宠物), finance(财务), document(证件), memorial(纪念), 
work(工作), study(学习), life(生活), entertainment(娱乐), shopping(购物), social(社交), other(其他)
也可以输入自定义分类，如：运动、阅读、旅行等（1-50个字符）"""
    )
    priority: int = Field(
        default=1, 
        ge=1, 
        le=3, 
        description="优先级（1-3）- 1=普通（蓝色）, 2=重要（橙色）, 3=紧急（红色）"
    )
    
    # ========== 周期设置 ==========
    recurrence_type: RecurrenceType = Field(
        default="once", 
        description="周期类型 - 可选值：once(单次), daily(每天), weekly(每周), monthly(每月), yearly(每年), custom(自定义间隔)"
    )
    recurrence_config: dict = Field(
        default_factory=dict, 
        description="""周期配置（JSON对象）- 根据类型提供不同配置：
weekly: {\"weekdays\": [1,3,5]} (周一三五)
monthly: {\"days\": [1,15]} (每月1号和15号)
yearly: {\"month\": 12, \"day\": 25} (每年12月25日)
custom: {\"interval\": 3, \"unit\": \"days\"} (每3天)
once/daily: {} (无需配置)"""
    )
    
    # ========== 提醒设置 ==========
    remind_channels: List[str] = Field(
        default=["app"], 
        description="""提醒渠道（数组，可多选）- app:APP推送(免费,默认), sms:短信(付费), wechat:微信服务号(需绑定), call:语音电话(付费)"""
    )
    advance_minutes: int = Field(
        default=0, 
        ge=0, 
        description="提前提醒分钟数 - 0:到点提醒, 30:提前30分钟, 60:提前1小时, 1440:提前1天"
    )
    
    # ========== 可选扩展信息 ==========
    amount: float | None = Field(
        None,
        ge=0,
        description="金额（以元为单位）- 用于财务类提醒，如房租 3000.00 元、买菜 50.5 元"
    )
    location: str | None = Field(
        None,
        max_length=200,
        description="位置信息（可选）- 简单文本地址，如'小区超市'、'公司食堂'、'健身房'、'北京市朝阳区xxx'"
    )
    notes: str | None = Field(
        None,
        max_length=500,
        description="备注信息（可选）- 用于记录额外说明，如'记得带会员卡'、'提前预约'"
    )
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v: str) -> str:
        """验证分类格式"""
        if not v or not v.strip():
            raise ValueError("分类不能为空")
        
        # 去除首尾空格
        v = v.strip()
        
        # 长度验证
        if len(v) > 50:
            raise ValueError("分类长度不能超过50个字符")
        
        # 推荐使用预设分类，但不强制（仅记录日志）
        if v not in RECOMMENDED_CATEGORIES:
            # 这里可以添加日志记录用户使用了自定义分类
            pass
        
        return v
    
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
    
    @field_validator('category', 'recurrence_type', mode='before')
    @classmethod
    def convert_enum_to_lowercase(cls, v):
        """
        枚举值预处理：强制转换为小写
        
        问题：数据库的ENUM类型是小写（'once', 'rent'），但前端可能传大写
        解决：在Pydantic验证之前，先将字符串转为小写
        """
        if v is None:
            return v
        if isinstance(v, str):
            return v.lower()  # "ONCE" -> "once", "RENT" -> "rent"
        if isinstance(v, enum.Enum):
            return v.value.lower() if isinstance(v.value, str) else v.value
        if hasattr(v, 'value'):
            val = v.value  # 如果已经是枚举对象，提取其值
            return val.lower() if isinstance(val, str) else val
        return v


class ReminderCreate(ReminderBase):
    """Reminder creation schema - 创建提醒
    
    时区处理说明：
    - 前端可传入任何格式的 ISO 8601 时间（带时区或不带时区）
    - 后端自动转换为 UTC 时间存储
    - 推荐格式："2025-12-31T10:00:00Z" (UTC) 或 "2025-12-31T18:00:00+08:00" (北京时间)
    """
    first_remind_time: datetime = Field(
        ..., 
        description="""首次提醒时间（必填，ISO 8601格式）
支持格式：
  - "2025-12-31T10:00:00Z" (UTC时间，推荐)
  - "2025-12-31T18:00:00+08:00" (带时区)
  - "2025-12-31T10:00:00" (无时区，视为UTC)
注意：必须是未来时间"""
    )
    
    @field_validator('first_remind_time', mode='after')
    @classmethod
    def normalize_datetime(cls, v: datetime) -> datetime:
        """统一时区处理：将任何格式的 datetime 转换为 UTC naive datetime（数据库格式）"""
        if v.tzinfo is not None:
            # 有时区：转换为 UTC 并移除时区信息
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        # 无时区：假定为 UTC
        return v
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "title": "交房租",
                    "description": "每月1号前交给房东",
                    "category": "rent",
                    "priority": 2,
                    "recurrence_type": "monthly",
                    "recurrence_config": {"days": [1]},
                    "remind_channels": ["app", "sms"],
                    "advance_minutes": 1440,
                    "amount": 300000,
                    "first_remind_time": "2025-01-01T09:00:00Z"
                },
                {
                    "title": "吃药提醒",
                    "description": "早中晚各一次",
                    "category": "health",
                    "priority": 3,
                    "recurrence_type": "daily",
                    "remind_channels": ["app"],
                    "first_remind_time": "2025-12-28T08:00:00Z"
                },
                {
                    "title": "周会提醒",
                    "category": "other",
                    "recurrence_type": "weekly",
                    "recurrence_config": {"weekdays": [1]},
                    "advance_minutes": 30,
                    "first_remind_time": "2025-12-30T14:00:00+08:00"
                }
            ],
            "description": """
时区处理说明：
- 前端可以传入任何格式的 ISO 8601 时间（带时区或不带）
- 推荐格式：\"2025-12-31T10:00:00Z\" (UTC) 或 \"2025-12-31T18:00:00+08:00\" (北京时间)
- 后端自动转换为 UTC 时间存储
- 枚举值使用小写字符串（如 \"once\", \"daily\" 等）
            """
        }


class ReminderUpdate(ReminderBase):
    """
    Reminder update schema - 更新提醒
    
    所有字段均可选，仅更新提供的字段，未提供的字段保持原值不变
    """
    title: str | None = Field(None, max_length=200, description="提醒标题")
    description: str | None = Field(None, max_length=1000, description="提醒描述")
    category: str | None = Field(None, min_length=1, max_length=50, description="分类（支持自定义）")
    priority: int | None = Field(None, ge=1, le=3, description="优先级")
    recurrence_type: RecurrenceType | None = Field(None, description="周期类型")
    recurrence_config: dict | None = Field(None, description="周期配置")
    remind_channels: List[str] | None = Field(None, description="提醒渠道")
    advance_minutes: int | None = Field(None, ge=0, description="提前提醒分钟数")
    amount: int | None = Field(None, description="金额（以分为单位）")
    location: dict | None = Field(None, description="位置信息")
    attachments: List[dict] | None = Field(None, description="附件列表")
    is_active: bool | None = Field(None, description="是否启用 - false表示暂停提醒")
    is_completed: bool | None = Field(None, description="是否已完成 - true表示标记为完成")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "交房租（已改为每月5号）",
                "recurrence_config": {"days": [5]},
                "advance_minutes": 2880
            },
            "description": "更新示例：PUT /api/v1/reminders/123 只传入需要修改的字段，如 {\"advance_minutes\": 60, \"remind_channels\": [\"app\", \"sms\"]}，其他字段保持不变"
        }
    
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
    """
    Reminder response schema - 提醒响应
    
    返回提醒的完整信息，包括系统生成的字段
    """
    id: int = Field(description="提醒ID（唯一标识）")
    user_id: int = Field(description="创建者用户ID")
    
    # 时间信息
    first_remind_time: datetime = Field(description="首次提醒时间")
    next_remind_time: datetime = Field(description="下次提醒时间（由系统自动计算）")
    last_remind_time: datetime | None = Field(None, description="上次提醒时间（首次提醒前为null）")
    
    # 状态信息
    is_active: bool = Field(description="是否启用 - false表示已暂停")
    is_completed: bool = Field(default=False, description="是否已完成")
    completed_at: datetime | None = Field(None, description="完成时间")
    
    # 审计时间
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="最后更新时间")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 123,
                "user_id": 1,
                "title": "交房租",
                "description": "每月1号前交给房东",
                "category": "rent",
                "priority": 2,
                "recurrence_type": "monthly",
                "recurrence_config": {"days": [1]},
                "remind_channels": ["app", "sms"],
                "advance_minutes": 1440,
                "amount": 300000,
                "location": None,
                "attachments": None,
                "first_remind_time": "2025-01-01T09:00:00",
                "next_remind_time": "2025-02-01T09:00:00",
                "last_remind_time": "2025-01-01T09:00:00",
                "is_active": True,
                "is_completed": False,
                "completed_at": None,
                "created_at": "2024-12-01T10:00:00",
                "updated_at": "2024-12-28T15:30:00"
            }
        }


class VoiceReminderCreate(BaseModel):
    """
    Voice input reminder creation schema - 语音创建提醒
    
    用户通过语音输入创建提醒，后端使用ASR+NLU解析
    """
    audio_base64: str = Field(
        ..., 
        description="Base64编码的音频数据（必填）- 前端录音后转为Base64字符串传入"
    )
    audio_format: str = Field(
        default="wav", 
        description="音频格式（默认wav）- 支持格式：wav, mp3, m4a"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",
                "audio_format": "wav"
            },
            "description": """语音创建提醒流程：
1. 前端录音（3-10秒）
2. 转为Base64编码
3. 调用 POST /api/v1/reminders/voice
4. 后端ASR识别 → NLU解析 → 自动创建提醒
5. 返回创建的提醒信息

示例语音：\"明天上午9点提醒我开会\" / \"每周一下午3点提醒我写周报\" / \"12月31号提醒我交房租3000元\""""
        }


class QuickReminderCreate(BaseModel):
    """
    Quick reminder creation from template - 从模板快速创建提醒
    
    选择系统模板或自定义模板，一键创建提醒
    """
    template_id: str = Field(
        ..., 
        description="""模板ID（必填）- 可通过以下接口获取：
GET /api/v1/templates/system - 系统模板
GET /api/v1/templates/custom - 我的自定义模板"""
    )
    custom_data: dict = Field(
        default_factory=dict, 
        description="""自定义数据（可选）- 覆盖模板的默认值
格式：{\"first_remind_time\": \"2025-12-31T09:00:00\", \"amount\": 300000, \"description\": \"自定义描述\"}"""
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "template_id": "template_rent_monthly",
                    "custom_data": {
                        "first_remind_time": "2025-01-01T09:00:00",
                        "amount": 300000
                    }
                },
                {
                    "template_id": "template_medicine_daily",
                    "custom_data": {
                        "first_remind_time": "2025-12-28T08:00:00"
                    }
                }
            ],
            "description": """快速创建流程：
1. 浏览模板列表
2. 选择模板
3. 可选：自定义部分字段（如时间、金额）
4. 一键创建

示例模板：交房租（每月1号）/ 吃药提醒（每天）/ 宠物疫苗（每年）/ 信用卡还款（每月）"""
        }
