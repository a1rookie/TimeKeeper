"""
User Schemas
用户相关的 Pydantic 模型
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
import re


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
    """User update schema"""
    nickname: str | None = Field(None, max_length=50, description="昵称")
    avatar_url: str | None = Field(None, max_length=255, description="头像URL")
    settings: dict | None = Field(None, description="用户设置")
    
    @validator('nickname')
    def validate_nickname(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('昵称不能为空')
        return v.strip() if v else v


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
    """User response schema"""
    id: int
    avatar_url: str | None = None
    settings: dict = {}
    is_active: bool = True
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
