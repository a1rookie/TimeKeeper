"""
Reminder API Endpoints
提醒相关的 API 端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.reminder import (
    ReminderCreate, 
    ReminderUpdate, 
    ReminderResponse,
    VoiceReminderCreate,
    QuickReminderCreate
)
from app.schemas.reminder_completion import (
    ReminderCompletionCreate,
    ReminderCompletionResponse
)
from app.repositories import get_reminder_repository, get_reminder_completion_repository
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.reminder_completion_repository import ReminderCompletionRepository
from app.services.push_task_service import create_push_task_for_reminder
from app.core.database import get_db
from app.core.recurrence import calculate_next_occurrence
from sqlalchemy.orm import Session

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.post("/", response_model=ApiResponse[ReminderResponse], status_code=status.HTTP_201_CREATED)
async def create_reminder(
    reminder_data: ReminderCreate,
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository),
    db: Session = Depends(get_db)
):
    """
    Create a new reminder
    创建新提醒
    
    Returns:
        ApiResponse[ReminderResponse]: 统一响应格式，data 为创建的提醒
    """
    # 使用Repository创建提醒
    new_reminder = reminder_repo.create(
        user_id=current_user.id,
        title=reminder_data.title,
        description=reminder_data.description,
        category=reminder_data.category,
        recurrence_type=reminder_data.recurrence_type,
        first_remind_time=reminder_data.first_remind_time,
        recurrence_config=reminder_data.recurrence_config,
        remind_channels=reminder_data.remind_channels,
        advance_minutes=reminder_data.advance_minutes,
        priority=reminder_data.priority,
        amount=reminder_data.amount,
        location=reminder_data.location,
        attachments=reminder_data.attachments
    )
    
    # 自动创建推送任务
    create_push_task_for_reminder(db, new_reminder)
    
    return ApiResponse.success(data=new_reminder, message="创建成功")


@router.get("/", response_model=ApiResponse[List[ReminderResponse]])
async def get_reminders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository)
):
    """
    Get user's reminders
    获取用户的提醒列表
    
    Returns:
        ApiResponse[List[ReminderResponse]]: 统一响应格式，data 为提醒列表
    """
    reminders = reminder_repo.get_user_reminders(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        is_active=is_active
    )
    return ApiResponse.success(data=reminders)


@router.get("/{reminder_id}", response_model=ApiResponse[ReminderResponse])
async def get_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository)
):
    """
    Get reminder by ID
    获取提醒详情
    
    Returns:
        ApiResponse[ReminderResponse]: 统一响应格式，data 为提醒详情
    """
    reminder = reminder_repo.get_by_id(reminder_id, current_user.id)
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    return ApiResponse.success(data=reminder)


@router.put("/{reminder_id}", response_model=ApiResponse[ReminderResponse])
async def update_reminder(
    reminder_id: int,
    reminder_data: ReminderUpdate,
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository)
):
    """
    Update reminder
    更新提醒
    
    Returns:
        ApiResponse[ReminderResponse]: 统一响应格式，data 为更新后的提醒
    """
    reminder = reminder_repo.get_by_id(reminder_id, current_user.id)
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    # Update fields
    update_data = reminder_data.model_dump(exclude_unset=True)
    updated_reminder = reminder_repo.update(reminder, **update_data)
    
    return ApiResponse.success(data=updated_reminder, message="更新成功")


@router.delete("/{reminder_id}", response_model=ApiResponse[None])
async def delete_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository)
):
    """
    Delete reminder
    删除提醒
    
    Returns:
        ApiResponse[None]: 统一响应格式，data 为空
    """
    reminder = reminder_repo.get_by_id(reminder_id, current_user.id)
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    reminder_repo.delete(reminder)
    
    return ApiResponse.success(message="删除成功")


@router.post("/{reminder_id}/complete", response_model=ApiResponse[ReminderResponse])
async def complete_reminder(
    reminder_id: int,
    completion_data: Optional[ReminderCompletionCreate] = None,
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository),
    completion_repo: ReminderCompletionRepository = Depends(get_reminder_completion_repository),
    db: Session = Depends(get_db)
):
    """
    Mark reminder as completed
    标记提醒为已完成
    
    业务逻辑：
    1. 标记提醒为已完成
    2. 记录完成记录到 reminder_completions 表
    3. 计算下次提醒时间
    4. 创建新的推送任务
    
    Returns:
        ApiResponse[ReminderResponse]: 统一响应格式，data 为更新后的提醒
    """
    # 1. 获取提醒
    reminder = reminder_repo.get_by_id(reminder_id, current_user.id)
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    # 2. 标记完成
    reminder = reminder_repo.mark_completed(reminder, current_user.id)
    
    # 3. 记录完成记录
    note = completion_data.note if completion_data else None
    completion_repo.create(
        reminder_id=reminder.id,
        user_id=current_user.id,
        scheduled_time=reminder.next_remind_time,
        note=note,
        status="completed"
    )
    
    # 4. 如果是周期性提醒，计算下次提醒时间
    if reminder.recurrence_type != "once":
        next_time = calculate_next_occurrence(
            reminder.next_remind_time,
            reminder.recurrence_type,
            reminder.recurrence_config
        )
        
        # 更新下次提醒时间，并重置完成状态
        reminder.next_remind_time = next_time
        reminder.last_remind_time = reminder.completed_at
        reminder.is_completed = False
        reminder.completed_at = None
        db.commit()
        db.refresh(reminder)
        
        # 5. 创建新的推送任务
        create_push_task_for_reminder(db, reminder)
    
    return ApiResponse.success(data=reminder, message="已标记为完成")


@router.post("/{reminder_id}/uncomplete", response_model=ApiResponse[ReminderResponse])
async def uncomplete_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository),
    completion_repo: ReminderCompletionRepository = Depends(get_reminder_completion_repository)
):
    """
    Mark reminder as uncompleted
    取消提醒完成状态
    
    Returns:
        ApiResponse[ReminderResponse]: 统一响应格式，data 为更新后的提醒
    """
    # 1. 获取提醒
    reminder = reminder_repo.get_by_id(reminder_id, current_user.id)
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    # 2. 取消完成状态
    reminder = reminder_repo.mark_uncompleted(reminder)
    
    # 3. 删除最新的完成记录
    completion_repo.delete_latest(reminder_id)
    
    return ApiResponse.success(data=reminder, message="已取消完成状态")


@router.get("/{reminder_id}/completions", response_model=ApiResponse[List[ReminderCompletionResponse]])
async def get_reminder_completions(
    reminder_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository),
    completion_repo: ReminderCompletionRepository = Depends(get_reminder_completion_repository)
):
    """
    Get reminder completion history
    获取提醒完成历史记录
    
    Returns:
        ApiResponse[List[ReminderCompletionResponse]]: 统一响应格式，data 为完成记录列表
    """
    # 验证提醒所有权
    reminder = reminder_repo.get_by_id(reminder_id, current_user.id)
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    # 获取完成记录
    completions = completion_repo.get_by_reminder(reminder_id, skip, limit)
    return ApiResponse.success(data=completions)


@router.post("/voice", response_model=ApiResponse[ReminderResponse], status_code=status.HTTP_201_CREATED)
async def create_reminder_from_voice(voice_data: VoiceReminderCreate, db: Session = Depends(get_db)):
    """
    Create reminder from voice input
    通过语音创建提醒
    
    Returns:
        ApiResponse[ReminderResponse]: 统一响应格式，data 为创建的提醒
    
    TODO: Implement voice recognition and NLP parsing
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="语音识别功能待实现"
    )


@router.post("/quick", response_model=ApiResponse[ReminderResponse], status_code=status.HTTP_201_CREATED)
async def create_quick_reminder(quick_data: QuickReminderCreate, db: Session = Depends(get_db)):
    """
    Create reminder from template
    从模板快速创建提醒
    
    Returns:
        ApiResponse[ReminderResponse]: 统一响应格式，data 为创建的提醒
    
    TODO: Implement template system
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="模板功能待实现"
    )
