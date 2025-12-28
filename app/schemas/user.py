"""
User Schemas
用户相关的 Pydantic 模型
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
import re


class UserSettings(BaseModel):
    """
    用户设置结构
    
    所有字段均可选，未设置时使用系统默认值
    更新规则：增量更新，只更新提供的字段
    """
    # ========== 通知设置 ==========
    enable_push_notification: bool = Field(
        True, 
        description="APP 推送通知开关（默认开启）- 控制是否接收 APP 内推送"
    )
    enable_sms_notification: bool = Field(
        False, 
        description="短信通知开关（默认关闭，需付费）- 控制是否接收短信提醒"
    )
    enable_wechat_notification: bool = Field(
        False, 
        description="微信通知开关（默认关闭）- 控制是否接收微信服务号消息"
    )
    enable_call_notification: bool = Field(
        False, 
        description="电话通知开关（默认关闭，需付费）- 控制是否接收语音电话提醒"
    )
    
    # ========== 提醒默认设置 ==========
    default_advance_minutes: int = Field(
        0, 
        ge=0, 
        le=1440, 
        description="默认提前提醒分钟数（0-1440分钟，即0-24小时）- 创建新提醒时的默认值"
    )
    default_remind_channels: list[str] = Field(
        ["app"], 
        description="默认提醒渠道列表 - 可选值: ['app', 'sms', 'wechat', 'call']，创建新提醒时的默认渠道"
    )
    
    # ========== 隐私设置 ==========
    allow_family_view_reminders: bool = Field(
        True, 
        description="家庭组可见性（默认开启）- 是否允许家庭组成员查看我的提醒"
    )
    allow_template_share: bool = Field(
        True, 
        description="模板分享权限（默认开启）- 是否允许他人使用我分享的自定义模板"
    )
    
    # ========== 界面设置 ==========
    theme: str = Field(
        "auto", 
        description="界面主题 - 可选值: 'light'(浅色), 'dark'(深色), 'auto'(跟随系统)"
    )
    language: str = Field(
        "zh-CN", 
        description="界面语言 - 可选值: 'zh-CN'(简体中文), 'en-US'(英语)"
    )
    
    # ========== 扩展设置 ==========
    extra: dict = Field(
        default_factory=dict, 
        description="其他自定义设置（预留字段）- 用于存储未来新增的配置项"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "enable_push_notification": True,
                "enable_sms_notification": False,
                "default_advance_minutes": 30,
                "default_remind_channels": ["app", "sms"],
                "allow_family_view_reminders": True,
                "allow_template_share": True,
                "theme": "dark",
                "language": "zh-CN",
                "extra": {}
            },
            "description": """
用户个性化设置完整结构：

1. 通知设置（决定接收哪些类型的通知）
   - enable_push_notification: APP推送（免费）
   - enable_sms_notification: 短信（按条收费）
   - enable_wechat_notification: 微信（需绑定）
   - enable_call_notification: 电话（按次收费）

2. 提醒默认设置（影响创建新提醒时的预填值）
   - default_advance_minutes: 提前提醒时间（0表示到点提醒）
   - default_remind_channels: 默认通知渠道组合

3. 隐私设置（控制数据分享范围）
   - allow_family_view_reminders: 家庭组成员是否可见我的提醒
   - allow_template_share: 是否允许分享我的模板给他人

4. 界面设置（个性化显示）
   - theme: 主题颜色（浅色/深色/自动）
   - language: 界面语言

更新示例：
PUT /api/v1/users/me
{
  "settings": {
    "theme": "dark",
    "enable_sms_notification": true
  }
}
注：只更新提供的字段，其他设置保持不变
            """
        }



def validate_password_strength(password: str) -> str:
    """
    验证密码强度
    
    要求：
    - 长度至少8位
    - 至少包含一个大写字母
    - 至少包含一个小写字母
    - 至少包含一个数字
    - 至少包含一个特殊字符 (!@#$%^&*()_+-=[]{}|;:,.<>?)
    """
    if len(password) < 8:
        raise ValueError('密码长度至少8位')
    
    if not re.search(r'[A-Z]', password):
        raise ValueError('密码必须包含至少一个大写字母')
    
    if not re.search(r'[a-z]', password):
        raise ValueError('密码必须包含至少一个小写字母')
    
    if not re.search(r'\d', password):
        raise ValueError('密码必须包含至少一个数字')
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        raise ValueError('密码必须包含至少一个特殊字符 (!@#$%^&*等)')
    
    return password


class UserBase(BaseModel):
    """User base schema"""
    phone: str = Field(..., description="手机号")
    nickname: str | None = Field(None, description="昵称")


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    sms_code: str | None = Field(None, description="短信验证码 - 注册时需要")
    
    @validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        return validate_password_strength(v)


class UserLogin(BaseModel):
    """User login schema - 支持密码登录或验证码登录"""
    phone: str = Field(..., description="手机号")
    password: str | None = Field(None, description="密码 - 密码登录时必填")
    sms_code: str | None = Field(None, description="短信验证码 - 验证码登录时必填")
    
    @validator('sms_code')
    def validate_login_method(cls, v, values):
        """验证必须提供密码或验证码之一"""
        password = values.get('password')
        if not password and not v:
            raise ValueError('必须提供密码或短信验证码')
        return v


class UserUpdate(BaseModel):
    """User update schema - 更新用户信息"""
    nickname: str | None = Field(None, max_length=50, description="昵称")
    avatar_url: str | None = Field(None, max_length=255, description="头像URL")
    settings: UserSettings | None = Field(None, description="用户设置（结构化）")
    
    @validator('nickname')
    def validate_nickname(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('昵称不能为空')
        return v.strip() if v else v
    
    class Config:
        json_schema_extra = {
            "example": {
                "nickname": "小明",
                "avatar_url": "https://example.com/avatar.jpg",
                "settings": {
                    "enable_push_notification": True,
                    "enable_sms_notification": True,
                    "default_advance_minutes": 30,
                    "theme": "dark"
                }
            }
        }


class ChangePasswordRequest(BaseModel):
    """修改密码请求（已登录用户）"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """验证新密码强度"""
        return validate_password_strength(v)


class ResetPasswordRequest(BaseModel):
    """重置密码请求（忘记密码）"""
    phone: str = Field(..., description="手机号")
    sms_code: str = Field(..., description="短信验证码")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """验证新密码强度"""
        return validate_password_strength(v)


class ChangePhoneRequest(BaseModel):
    """修改手机号请求"""
    old_phone_sms_code: str = Field(..., description="旧手机号验证码")
    new_phone: str = Field(..., description="新手机号")
    new_phone_sms_code: str = Field(..., description="新手机号验证码")


class DeleteAccountRequest(BaseModel):
    """注销账号请求"""
    sms_code: str = Field(..., description="短信验证码")
    reason: str | None = Field(None, max_length=200, description="注销原因")


class UserResponse(UserBase):
    """User response schema - 用户信息响应"""
    id: int
    avatar_url: str | None = None
    settings: UserSettings = Field(default_factory=UserSettings, description="用户设置")
    
    # 账号状态
    is_active: bool = True
    is_verified: bool = True
    is_banned: bool = False
    role: str = "USER"  # 用户角色: USER, ADMIN, SUPER_ADMIN
    ban_reason: str | None = None
    banned_at: datetime | None = None
    
    # 登录信息
    last_login_at: datetime | None = None
    last_login_ip: str | None = None
    
    # 时间戳
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload schema"""
    user_id: int | None = None


class SendSmsRequest(BaseModel):
    """发送短信验证码请求"""
    phone: str = Field(..., description="手机号")
    purpose: str | None = Field("register", description="用途: register(注册) | login(登录) | reset(重置密码)")
