"""
Template Schemas
模板相关的 Pydantic 模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.template_share import ShareType


# ==================== 系统模板 ====================

class ReminderTemplateResponse(BaseModel):
    """系统模板响应"""
    id: int
    name: str
    category: str
    description: Optional[str]
    default_recurrence_type: Optional[str]
    default_recurrence_config: Optional[dict]
    default_remind_advance_days: int | None = None
    usage_count: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 用户自定义模板 ====================

class UserCustomTemplateCreate(BaseModel):
    """创建用户自定义模板"""
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, max_length=500, description="模板描述")
    recurrence_type: Optional[str] = Field(None, description="周期类型")
    recurrence_config: Optional[dict] = Field(None, description="周期配置")
    remind_advance_days: int = Field(0, ge=0, description="提前提醒天数")
    created_from_template_id: Optional[int] = Field(None, description="基于的系统模板ID")


class UserCustomTemplateUpdate(BaseModel):
    """更新用户自定义模板"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    recurrence_type: Optional[str] = None
    recurrence_config: Optional[dict] = None
    remind_advance_days: Optional[int] = Field(None, ge=0)


class UserCustomTemplateResponse(BaseModel):
    """用户自定义模板响应"""
    id: int
    user_id: int
    name: str
    description: Optional[str]
    recurrence_type: Optional[str]
    recurrence_config: Optional[dict]
    remind_advance_days: int | None = None
    created_from_template_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 模板分享 ====================

class TemplateShareCreate(BaseModel):
    """创建模板分享"""
    template_id: int = Field(..., description="模板ID（用户自定义模板）")
    share_type: ShareType = Field(..., description="分享类型")
    share_title: str = Field(..., min_length=1, max_length=100, description="分享标题")
    share_description: Optional[str] = Field(None, max_length=500, description="分享描述")
    family_group_id: Optional[int] = Field(None, description="家庭组ID（仅家庭分享需要）")


class TemplateShareResponse(BaseModel):
    """模板分享响应"""
    id: int
    template_id: int
    user_id: int
    share_type: ShareType
    share_code: str
    share_title: str
    share_description: Optional[str]
    family_group_id: Optional[int]
    usage_count: int
    like_count: int
    is_active: bool
    created_at: datetime
    # 关联信息
    owner_nickname: Optional[str] = None
    template_name: Optional[str] = None

    class Config:
        from_attributes = True


class TemplateShareDetail(TemplateShareResponse):
    """模板分享详情（包含完整模板信息）"""
    template: Optional[UserCustomTemplateResponse] = None
    is_liked: bool = False  # 当前用户是否点赞

    class Config:
        from_attributes = True


# ==================== 模板使用记录 ====================

class TemplateUsageCreate(BaseModel):
    """使用模板记录"""
    share_code: str = Field(..., description="分享码")
    feedback_rating: Optional[int] = Field(None, ge=1, le=5, description="评分 1-5")
    feedback_comment: Optional[str] = Field(None, max_length=500, description="评价内容")


class TemplateUsageResponse(BaseModel):
    """模板使用记录响应"""
    id: int
    template_share_id: int
    user_id: int
    feedback_rating: Optional[int]
    feedback_comment: Optional[str]
    used_at: datetime

    class Config:
        from_attributes = True


# ==================== 模板点赞 ====================

class TemplateLikeResponse(BaseModel):
    """模板点赞响应"""
    id: int
    template_share_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
