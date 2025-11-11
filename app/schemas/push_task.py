"""
Push Task Pydantic Schemas
推送任务数据验证模型
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.models.push_task import PushStatus


class PushTaskBase(BaseModel):
    """推送任务基础模型"""
    reminder_id: int = Field(..., description="关联的提醒ID")
    title: str = Field(..., min_length=1, max_length=200, description="推送标题")
    content: str = Field(..., min_length=1, max_length=1000, description="推送内容")
    scheduled_time: datetime = Field(..., description="计划推送时间")


class PushTaskCreate(BaseModel):
    """创建推送任务"""
    reminder_id: int = Field(..., description="关联的提醒ID")
    scheduled_time: datetime = Field(..., description="计划推送时间")


class PushTaskUpdate(BaseModel):
    """更新推送任务"""
    scheduled_time: Optional[datetime] = Field(None, description="计划推送时间")
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="推送标题")
    content: Optional[str] = Field(None, min_length=1, max_length=1000, description="推送内容")


class PushTaskResponse(BaseModel):
    """推送任务响应"""
    id: int
    user_id: int
    reminder_id: int
    title: str
    content: str
    channels: List[str]
    priority: int = 1
    scheduled_time: datetime
    sent_time: Optional[datetime] = None
    status: PushStatus
    error_message: Optional[str] = None
    retry_count: int
    max_retries: int = 3
    push_response: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PushTaskList(BaseModel):
    """推送任务列表响应"""
    tasks: List[PushTaskResponse]
    total: int
    skip: int
    limit: int
