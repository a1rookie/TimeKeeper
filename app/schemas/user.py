"""
User Schemas
用户相关的 Pydantic 模型
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """User base schema"""
    phone: str = Field(..., description="手机号")
    nickname: Optional[str] = Field(None, description="昵称")


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=6, description="密码")


class UserLogin(BaseModel):
    """User login schema"""
    phone: str = Field(..., description="手机号")
    password: str = Field(..., description="密码")


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
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload schema"""
    user_id: Optional[int] = None
