"""
Reminder Completion API
提醒完成记录的 API 路由
"""
from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.reminder_completion import CompletionStatus
from app.schemas.response import ApiResponse
from app.schemas.completion import (
    ReminderCompletionCreate,
    ReminderCompletionResponse,
    ReminderStats,
    UserStats
)
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.reminder_completion_repository import ReminderCompletionRepository
from app.repositories.family_member_repository import FamilyMemberRepository
from app.services.recurrence_service import RecurrenceService

router = APIRouter()


@router.post("/completions", response_model=ApiResponse[ReminderCompletionResponse], status_code=status.HTTP_201_CREATED)
async def complete_reminder(
    data: ReminderCompletionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    确认完成提醒
    - 记录完成时间和状态
    - 触发下次周期计算
    - 如果是家庭共享提醒，通知其他成员
    """
    reminder_repo = ReminderRepository(db)
    completion_repo = ReminderCompletionRepository(db)
    family_member_repo = FamilyMemberRepository(db)
    recurrence_service = RecurrenceService()
    
    # 检查提醒是否存在
    reminder = await reminder_repo.get_by_id(data.reminder_id)
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    # 检查权限
    can_complete = False
    
    # 1. 是否为提醒所有者
    if reminder.user_id == current_user.id:
        can_complete = True
    
    # 2. 如果是家庭共享提醒，检查是否为家庭成员
    if not can_complete and reminder.family_group_id:
        if await family_member_repo.is_member(reminder.family_group_id, current_user.id):
            can_complete = True
    
    if not can_complete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权完成该提醒"
        )
    
    # 检查是否已经记录了该时间点的完成
    existing = completion_repo.check_recent_completion(
        data.reminder_id,
        data.scheduled_time
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该提醒已经被标记为完成"
        )
    
    # 创建完成记录
    completion = await completion_repo.create(
        reminder_id=data.reminder_id,
        user_id=current_user.id,
        scheduled_time=data.scheduled_time,
        status=data.status
    )
    
    # 如果是周期性提醒，计算下次提醒时间
    if reminder.recurrence_type and reminder.recurrence_type != 'once':
        next_time = recurrence_service.calculate_next_time(
            recurrence_type=reminder.recurrence_type,
            recurrence_config=reminder.recurrence_config,
            current_time=data.scheduled_time
        )
        
        if next_time:
            # 更新下次提醒时间
            reminder_repo.update(
                reminder_id=reminder.id,
                next_remind_time=next_time
            )
            
            # TODO: 创建新的推送任务
            # from app.repositories.push_task_repository import PushTaskRepository
            # push_task_repo = PushTaskRepository(db)
            # push_task_repo.create_for_reminder(reminder, next_time)
    
    # TODO: 如果是家庭共享提醒，通知其他成员
    # if reminder.family_group_id:
    #     notify_family_members(reminder, completion, current_user)
    
    return ApiResponse.success(data=ReminderCompletionResponse(
        id=completion.id,
        reminder_id=completion.reminder_id,
        user_id=completion.user_id,
        scheduled_time=completion.scheduled_time,
        completed_time=completion.completed_time,
        status=completion.status,
        delay_minutes=completion.delay_minutes,
        created_at=completion.created_at
    ))


@router.get("/completions/reminder/{reminder_id}", response_model=ApiResponse[List[ReminderCompletionResponse]])
async def get_reminder_completions(
    reminder_id: int,
    limit: int = Query(50, ge=1, le=100, description="返回记录数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询提醒的完成记录
    """
    reminder_repo = ReminderRepository(db)
    completion_repo = ReminderCompletionRepository(db)
    
    # 检查提醒是否存在
    reminder = await reminder_repo.get_by_id(reminder_id)
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    # 检查权限（所有者或家庭成员可查看）
    can_view = reminder.user_id == current_user.id
    if not can_view and reminder.family_group_id:
        family_member_repo = FamilyMemberRepository(db)
        can_view = await family_member_repo.is_member(reminder.family_group_id, current_user.id)
    
    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看该提醒的完成记录"
        )
    
    completions = await completion_repo.get_by_reminder(reminder_id, limit=limit)
    
    return ApiResponse.success(data=[
        ReminderCompletionResponse(
            id=c.id,
            reminder_id=c.reminder_id,
            user_id=c.user_id,
            scheduled_time=c.scheduled_time,
            completed_time=c.completed_time,
            status=c.status,
            delay_minutes=c.delay_minutes,
            created_at=c.created_at
        ) for c in completions
    ])


@router.get("/completions/my", response_model=ApiResponse[List[ReminderCompletionResponse]])
async def get_my_completions(
    days: int = Query(30, ge=1, le=365, description="查询天数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询我的完成记录
    """
    completion_repo = ReminderCompletionRepository(db)
    completions = await completion_repo.get_by_user(current_user.id, days=days)
    
    return ApiResponse.success(data=[
        ReminderCompletionResponse(
            id=c.id,
            reminder_id=c.reminder_id,
            user_id=c.user_id,
            scheduled_time=c.scheduled_time,
            completed_time=c.completed_time,
            status=c.status,
            delay_minutes=c.delay_minutes,
            created_at=c.created_at
        ) for c in completions
    ])


@router.get("/stats/reminder/{reminder_id}", response_model=ApiResponse[ReminderStats])
async def get_reminder_stats(
    reminder_id: int,
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询提醒的统计信息
    """
    reminder_repo = ReminderRepository(db)
    completion_repo = ReminderCompletionRepository(db)
    
    reminder = await reminder_repo.get_by_id(reminder_id)
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    # 检查权限
    can_view = reminder.user_id == current_user.id
    if not can_view and reminder.family_group_id:
        family_member_repo = FamilyMemberRepository(db)
        can_view = await family_member_repo.is_member(reminder.family_group_id, current_user.id)
    
    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看该提醒的统计"
        )
    
    # 获取统计数据
    completions = await completion_repo.get_by_reminder(reminder_id, limit=1000)
    
    # 筛选指定天数内的记录
    since = datetime.utcnow() - timedelta(days=days)
    recent_completions = [c for c in completions if c.scheduled_time >= since]
    
    total_count = len(recent_completions)
    completed_count = sum(1 for c in recent_completions if c.status in [CompletionStatus.COMPLETED, CompletionStatus.DELAYED])
    delayed_count = sum(1 for c in recent_completions if c.status == CompletionStatus.DELAYED)
    skipped_count = sum(1 for c in recent_completions if c.status == CompletionStatus.SKIPPED)
    
    completion_rate = await completion_repo.get_completion_rate(reminder_id, days=days)
    avg_delay = await completion_repo.get_avg_delay_time(reminder_id, days=days)
    
    return ApiResponse.success(data=ReminderStats(
        reminder_id=reminder_id,
        total_count=total_count,
        completed_count=completed_count,
        delayed_count=delayed_count,
        skipped_count=skipped_count,
        completion_rate=completion_rate,
        avg_delay_minutes=avg_delay
    ))


@router.get("/stats/my", response_model=ApiResponse[UserStats])
async def get_my_stats(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询我的整体统计信息
    """
    reminder_repo = ReminderRepository(db)
    completion_repo = ReminderCompletionRepository(db)
    
    # 统计提醒数量
    all_reminders = await reminder_repo.get_by_user(current_user.id)
    active_reminders = [r for r in all_reminders if r.is_active]
    
    # 统计完成记录
    completions = await completion_repo.get_by_user(current_user.id, days=days)
    total_completions = len(completions)
    
    # 计算完成率
    completion_rate = await completion_repo.get_user_completion_rate(current_user.id, days=days)
    
    # 计算平均延迟时间
    delayed_completions = [c for c in completions if c.status == CompletionStatus.DELAYED and c.delay_minutes]
    avg_delay = int(sum(c.delay_minutes for c in delayed_completions) / len(delayed_completions)) if delayed_completions else 0
    
    return ApiResponse.success(data=UserStats(
        user_id=current_user.id,
        total_reminders=len(all_reminders),
        active_reminders=len(active_reminders),
        total_completions=total_completions,
        completion_rate=completion_rate,
        avg_delay_minutes=avg_delay
    ))
