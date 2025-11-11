"""
Reminder API Endpoints
提醒相关的 API 端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.reminder import Reminder
from app.schemas.reminder import (
    ReminderCreate, 
    ReminderUpdate, 
    ReminderResponse,
    VoiceReminderCreate,
    QuickReminderCreate
)

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.post("/", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    reminder_data: ReminderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new reminder
    创建新提醒
    """
    new_reminder = Reminder(
        user_id=current_user.id,
        title=reminder_data.title,
        description=reminder_data.description,
        category=reminder_data.category,
        recurrence_type=reminder_data.recurrence_type,
        recurrence_config=reminder_data.recurrence_config,
        first_remind_time=reminder_data.first_remind_time,
        next_remind_time=reminder_data.first_remind_time,
        remind_channels=reminder_data.remind_channels,
        advance_minutes=reminder_data.advance_minutes
    )
    
    db.add(new_reminder)
    db.commit()
    db.refresh(new_reminder)
    
    return new_reminder


@router.get("/", response_model=List[ReminderResponse])
async def get_reminders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's reminders
    获取用户的提醒列表
    """
    query = db.query(Reminder).filter(Reminder.user_id == current_user.id)
    
    if is_active is not None:
        query = query.filter(Reminder.is_active == is_active)
    
    reminders = query.order_by(Reminder.next_remind_time).offset(skip).limit(limit).all()
    return reminders


@router.get("/{reminder_id}", response_model=ReminderResponse)
async def get_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get reminder by ID
    获取提醒详情
    """
    reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id,
        Reminder.user_id == current_user.id
    ).first()
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    return reminder


@router.put("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: int,
    reminder_data: ReminderUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update reminder
    更新提醒
    """
    reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id,
        Reminder.user_id == current_user.id
    ).first()
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    # Update fields
    update_data = reminder_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reminder, field, value)
    
    db.commit()
    db.refresh(reminder)
    
    return reminder


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete reminder
    删除提醒
    """
    reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id,
        Reminder.user_id == current_user.id
    ).first()
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    db.delete(reminder)
    db.commit()
    
    return None


@router.post("/voice", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder_from_voice(voice_data: VoiceReminderCreate, db: Session = Depends(get_db)):
    """
    Create reminder from voice input
    通过语音创建提醒
    
    TODO: Implement voice recognition and NLP parsing
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="语音识别功能待实现"
    )


@router.post("/quick", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_quick_reminder(quick_data: QuickReminderCreate, db: Session = Depends(get_db)):
    """
    Create reminder from template
    从模板快速创建提醒
    
    TODO: Implement template system
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="模板功能待实现"
    )
