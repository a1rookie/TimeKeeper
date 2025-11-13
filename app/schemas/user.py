"""
User Schemas
用户相关的 Pydantic 模型
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """User base schema"""
    phone: str = Field(..., description="手机号")
    nickname: Optional[str] = Field(None, description="昵称")


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=6, description="密码")
    sms_code: Optional[str] = Field(None, description="短信验证码 - 注册时需要")


class UserLogin(BaseModel):
    """User login schema - 支持密码登录或验证码登录"""
    phone: str = Field(..., description="手机号")
    password: Optional[str] = Field(None, description="密码 - 密码登录时必填")
    sms_code: Optional[str] = Field(None, description="短信验证码 - 验证码登录时必填")
    
    @validator('sms_code')
    def validate_login_method(cls, v, values):
        """验证必须提供密码或验证码之一"""
        password = values.get('password')
        if not password and not v:
            raise ValueError('必须提供密码或短信验证码')
        return v


class UserUpdate(BaseModel):
    """User update schema"""
    nickname: Optional[str] = Field(None, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    settings: Optional[dict] = Field(None, description="用户设置")


class UserResponse(UserBase):
    """User response schema"""
    id: int
    avatar_url: Optional[str] = None
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
    user_id: Optional[int] = None


class SendSmsRequest(BaseModel):
    """发送短信验证码请求"""
    phone: str = Field(..., description="手机号")
    purpose: Optional[str] = Field("register", description="用途: register(注册) | login(登录) | reset(重置密码)")
