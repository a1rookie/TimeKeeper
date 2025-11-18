"""
Reminder Completion Schemas
提醒完成记录相关的 Pydantic 模型
"""
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.reminder_completion import CompletionStatus


class ReminderCompletionCreate(BaseModel):
    """创建完成记录"""
    reminder_id: int = Field(..., description="提醒ID")
    scheduled_time: datetime = Field(..., description="计划提醒时间")
    status: CompletionStatus = Field(CompletionStatus.COMPLETED, description="完成状态")


class ReminderCompletionResponse(BaseModel):
    """完成记录响应"""
    id: int
    reminder_id: int
    user_id: int
    scheduled_time: datetime | None = None
    completed_time: datetime
    status: CompletionStatus
    delay_minutes: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReminderStats(BaseModel):
    """提醒统计信息"""
    reminder_id: int
    total_count: int = Field(..., description="总次数")
    completed_count: int = Field(..., description="完成次数")
    delayed_count: int = Field(..., description="延迟次数")
    skipped_count: int = Field(..., description="跳过次数")
    completion_rate: float = Field(..., description="完成率(%)")
    avg_delay_minutes: int = Field(..., description="平均延迟时间(分钟)")


class UserStats(BaseModel):
    """用户统计信息"""
    user_id: int
    total_reminders: int = Field(..., description="总提醒数")
    active_reminders: int = Field(..., description="活跃提醒数")
    total_completions: int = Field(..., description="总完成次数")
    completion_rate: float = Field(..., description="完成率(%)")
    avg_delay_minutes: int = Field(..., description="平均延迟时间(分钟)")
