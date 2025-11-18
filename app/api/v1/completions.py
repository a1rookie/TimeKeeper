"""
Reminder Completion API
提醒完成记录的 API 路由
"""
from typing import List
from datetime import datetime, timedelta, UTC
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.response import ApiResponse

logger = structlog.get_logger(__name__)
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
) -> ApiResponse[ReminderCompletionResponse]:
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
    user_id = int(current_user.id)
    reminder = await reminder_repo.get_by_id(data.reminder_id, user_id)
    
    # 如果不是所有者，尝试通过family查找
    if not reminder:
        # 尝试查询所有提醒（不限制user_id）来检查family权限
        reminder = await reminder_repo.get_by_id_without_user_check(data.reminder_id)
        
        if not reminder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="提醒不存在"
            )
    
    # 检查权限
    can_complete = False
    
    # 1. 是否为提醒所有者
    if int(reminder.user_id) == user_id:
        can_complete = True
    
    # 2. 如果是家庭共享提醒，检查是否为家庭成员
    family_group_id_val = int(reminder.family_group_id) if reminder.family_group_id else None  
    if not can_complete and family_group_id_val:
        family_group_id = int(family_group_id_val)
        if await family_member_repo.is_member(family_group_id, user_id):
            can_complete = True
    
    if not can_complete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权完成该提醒"
        )
    
    # 检查是否已经记录了该时间点的完成（简化检查，查询最近的完成记录）
    existing = await completion_repo.check_recent_completion(
        reminder_id=data.reminder_id,
        scheduled_time=data.scheduled_time,
        time_window_hours=1
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该提醒已经被标记为完成"
        )
    
    # 创建完成记录
    completion = await completion_repo.create(
        reminder_id=data.reminder_id,
        user_id=user_id,
        scheduled_time=data.scheduled_time,
        status=data.status.value if hasattr(data.status, 'value') else str(data.status)
    )
    
    # 如果是周期性提醒，计算下次提醒时间
    recurrence_type_val = str(reminder.recurrence_type) if reminder.recurrence_type else None  
    if recurrence_type_val and recurrence_type_val != 'once':
        recurrence_config_val = reminder.recurrence_config or {}
        next_time = recurrence_service.calculate_next_time(
            recurrence_type=recurrence_type_val,
            recurrence_config=recurrence_config_val,
            current_time=data.scheduled_time
        )
        
        if next_time:
            # 更新下次提醒时间
            await reminder_repo.update(
                reminder=reminder,
                next_remind_time=next_time
            )
            
            # 创建新的推送任务
            from app.services.push_scheduler import create_push_task_for_reminder
            reminder_id = int(reminder.id)  
            reminder_user_id = int(reminder.user_id)  
            await create_push_task_for_reminder(db, reminder_id, reminder_user_id, next_time)
    
    # 如果是家庭共享提醒，通知其他家庭成员
    family_group_id_val = int(reminder.family_group_id) if reminder.family_group_id else None  
    if family_group_id_val:
        from app.services.family_notification_service import get_notification_service
        
        notification_service = get_notification_service(db)
        family_group_id = int(family_group_id_val)  
        reminder_id = int(reminder.id)  
        completion_id = int(completion.id)  
        reminder_title = str(reminder.title)  
        await notification_service.notify_reminder_completed(
            family_group_id=family_group_id,
            sender_id=user_id,
            reminder_id=reminder_id,
            completion_id=completion_id,
            reminder_title=reminder_title,
            completed_status=data.status.value if hasattr(data.status, 'value') else str(data.status)
        )
        
        logger.info(
            "family_reminder_completed",
            reminder_id=reminder_id,
            family_group_id=family_group_id,
            completed_by=user_id,
            event="family_reminder_completion"
        )
    
    return ApiResponse[ReminderCompletionResponse].success(data=ReminderCompletionResponse(
        id=int(completion.id),  
        reminder_id=int(completion.reminder_id),  
        user_id=int(completion.user_id),  
        scheduled_time=completion.scheduled_time,  
        completed_time=completion.completed_time,  
        status=completion.status,  
        delay_minutes=int(completion.delay_minutes) if completion.delay_minutes else None,  
        created_at=completion.created_at  
    ))


@router.get("/completions/reminder/{reminder_id}", response_model=ApiResponse[List[ReminderCompletionResponse]])
async def get_reminder_completions(
    reminder_id: int,
    limit: int = Query(50, ge=1, le=100, description="返回记录数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ApiResponse[List[ReminderCompletionResponse]]:
    """
    查询提醒的完成记录
    """
    reminder_repo = ReminderRepository(db)
    completion_repo = ReminderCompletionRepository(db)
    user_id = int(current_user.id)  
    
    # 检查提醒是否存在
    reminder = await reminder_repo.get_by_id(reminder_id, user_id)
    
    # 如果不是所有者，尝试通过family查找
    if not reminder:
        reminder = await reminder_repo.get_by_id_without_user_check(reminder_id)
        
        if not reminder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="提醒不存在"
            )
    
    # 检查权限（所有者或家庭成员可查看）
    can_view = int(reminder.user_id) == user_id  
    family_group_id_check = int(reminder.family_group_id) if reminder.family_group_id else None  
    if not can_view and family_group_id_check:
        family_member_repo = FamilyMemberRepository(db)
        assert reminder.family_group_id is not None
        family_group_id = int(reminder.family_group_id)  
        can_view = await family_member_repo.is_member(family_group_id, user_id)
    
    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看该提醒的完成记录"
        )
    
    completions = await completion_repo.get_by_reminder(reminder_id, limit=limit)
    
    return ApiResponse[List[ReminderCompletionResponse]].success(data=[
        ReminderCompletionResponse(
            id=int(c.id),  
            reminder_id=int(c.reminder_id),  
            user_id=int(c.user_id),  
            scheduled_time=c.scheduled_time,  
            completed_time=c.completed_time,  
            status=c.status,  
            delay_minutes=int(c.delay_minutes) if c.delay_minutes else None,  
            created_at=c.created_at  
        ) for c in completions
    ])


@router.get("/completions/my", response_model=ApiResponse[List[ReminderCompletionResponse]])
async def get_my_completions(
    days: int = Query(30, ge=1, le=365, description="查询天数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ApiResponse[List[ReminderCompletionResponse]]:
    """
    查询我的完成记录
    """
    completion_repo = ReminderCompletionRepository(db)
    user_id = int(current_user.id)  
    
    # 查询最近N天的完成记录
    since = datetime.now(UTC) - timedelta(days=days)
    completions = await completion_repo.get_by_user_since(user_id, since, limit=1000)
    
    return ApiResponse[List[ReminderCompletionResponse]].success(data=[
        ReminderCompletionResponse(
            id=int(c.id),  
            reminder_id=int(c.reminder_id),  
            user_id=int(c.user_id),  
            scheduled_time=c.scheduled_time,  
            completed_time=c.completed_time,  
            status=c.status,  
            delay_minutes=int(c.delay_minutes) if c.delay_minutes else None,  
            created_at=c.created_at  
        ) for c in completions
    ])


@router.get("/stats/reminder/{reminder_id}", response_model=ApiResponse[ReminderStats])
async def get_reminder_stats(
    reminder_id: int,
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ApiResponse[ReminderStats]:
    """
    查询提醒的统计信息
    """
    reminder_repo = ReminderRepository(db)
    completion_repo = ReminderCompletionRepository(db)
    user_id = int(current_user.id)  
    
    reminder = await reminder_repo.get_by_id(reminder_id, user_id)
    
    # 如果不是所有者，尝试通过family查找
    if not reminder:
        reminder = await reminder_repo.get_by_id_without_user_check(reminder_id)
        
        if not reminder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="提醒不存在"
            )
    
    # 检查权限
    can_view = int(reminder.user_id) == user_id  
    family_group_id_stats = int(reminder.family_group_id) if reminder.family_group_id else None  
    if not can_view and family_group_id_stats:
        family_member_repo = FamilyMemberRepository(db)
        family_group_id = int(family_group_id_stats)  
        can_view = await family_member_repo.is_member(family_group_id, user_id)
    
    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看该提醒的统计"
        )
    
    # 获取统计数据
    completions = await completion_repo.get_by_reminder(reminder_id, limit=1000)
    
    # 筛选指定天数内的记录
    since = datetime.now(UTC) - timedelta(days=days)
    recent_completions = [
        c for c in completions 
        if c.scheduled_time and c.scheduled_time >= since  
    ]
    
    total_count = len(recent_completions)
    completed_count = sum(
        1 for c in recent_completions 
        if str(c.status) in ["completed", "delayed"]  
    )
    delayed_count = sum(
        1 for c in recent_completions 
        if str(c.status) == "delayed"  
    )
    skipped_count = sum(
        1 for c in recent_completions 
        if str(c.status) == "skipped"  
    )
    
    # 计算完成率
    completion_rate = (completed_count / total_count * 100) if total_count > 0 else 0.0
    
    # 计算平均延迟
    delayed_records = [
        c for c in recent_completions 
        if c.delay_minutes and int(c.delay_minutes) > 0  
    ]
    avg_delay = (
        int(sum(int(c.delay_minutes) for c in delayed_records) / len(delayed_records))  
        if delayed_records else 0
    )
    
    return ApiResponse[ReminderStats].success(data=ReminderStats(
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
) -> ApiResponse[UserStats]:
    """
    查询我的整体统计信息
    """
    reminder_repo = ReminderRepository(db)
    completion_repo = ReminderCompletionRepository(db)
    user_id = int(current_user.id)  
    
    # 统计提醒数量
    all_reminders = await reminder_repo.get_user_reminders(user_id, limit=10000)
    active_reminders = [r for r in all_reminders if r.is_active]  
    
    # 统计完成记录
    since = datetime.now(UTC) - timedelta(days=days)
    completions = await completion_repo.get_by_user_since(user_id, since, limit=10000)
    total_completions = len(completions)
    
    # 计算完成率（假设每个提醒每天应完成一次，简化计算）
    expected_completions = len(active_reminders) * days
    completion_rate = (
        (total_completions / expected_completions * 100) 
        if expected_completions > 0 else 0.0
    )
    
    # 计算平均延迟时间
    delayed_completions = [
        c for c in completions 
        if c.delay_minutes and int(c.delay_minutes) > 0  
    ]
    avg_delay = (
        int(sum(int(c.delay_minutes) for c in delayed_completions) / len(delayed_completions))  
        if delayed_completions else 0
    )
    
    return ApiResponse[UserStats].success(data=UserStats(
        user_id=user_id,
        total_reminders=len(all_reminders),
        active_reminders=len(active_reminders),
        total_completions=total_completions,
        completion_rate=completion_rate,
        avg_delay_minutes=avg_delay
    ))
