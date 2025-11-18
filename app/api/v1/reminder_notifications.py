"""
Reminder Notification API
提醒通知策略的 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.reminder_notification import (
    ReminderNotificationCreate,
    ReminderNotificationUpdate,
    ReminderNotificationResponse,
    NotificationScheduleResponse
)
from app.repositories.reminder_notification_repository import ReminderNotificationRepository
from app.repositories.reminder_repository import ReminderRepository
from app.services.advanced_notification_service import get_advanced_notification_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/reminders", tags=["Reminder Notifications"])


@router.post("/{reminder_id}/notification-config", response_model=ApiResponse[ReminderNotificationResponse], status_code=status.HTTP_201_CREATED)
async def create_notification_config(
    reminder_id: int,
    config: ReminderNotificationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[ReminderNotificationResponse]:
    """
    为提醒创建通知策略
    
    支持的功能:
    - 提前通知：提前N天开始通知，每M天通知一次
    - 当天多次通知：当天指定多个时间点通知
    - 智能时间调整：自动避免夜间通知（22:00-07:00）
    - 自定义消息模板
    
    示例1 - 生日提醒（提前5天，每2天通知）:
    ```json
    {
      "advance_notify_enabled": true,
      "advance_days": 5,
      "advance_notify_interval": 2,
      "advance_notify_time": "09:00",
      "same_day_notifications": ["09:00", "12:00"],
      "avoid_night_time": true
    }
    ```
    
    示例2 - 吃药提醒（提前1小时 + 准时）:
    ```json
    {
      "advance_notify_enabled": false,
      "same_day_notifications": ["19:00", "20:00"],
      "avoid_night_time": false
    }
    ```
    """
    # 检查提醒是否存在
    user_id = int(current_user.id)  
    reminder_repo = ReminderRepository(db)
    reminder = await reminder_repo.get_by_id(reminder_id, user_id)
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    # 检查是否已有配置
    notification_repo = ReminderNotificationRepository(db)
    existing = await notification_repo.get_by_reminder_id(reminder_id)
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该提醒已有通知策略，请使用更新接口"
        )
    
    # 创建配置
    notification_config = await notification_repo.create(
        reminder_id=reminder_id,
        advance_notify_enabled=config.advance_notify_enabled,
        advance_days=config.advance_days,
        advance_notify_interval=config.advance_notify_interval,
        advance_notify_time=config.advance_notify_time,
        same_day_notifications=config.same_day_notifications,
        avoid_night_time=config.avoid_night_time,
        night_time_fallback=config.night_time_fallback,
        custom_message_template=config.custom_message_template
    )
    
    logger.info(
        "notification_config_created",
        reminder_id=reminder_id,
        user_id=current_user.id,
        advance_enabled=config.advance_notify_enabled,
        advance_days=config.advance_days,
        event="notification_config_create"
    )
    
    return ApiResponse[ReminderNotificationResponse].success(
        data=ReminderNotificationResponse.model_validate(notification_config),
        message="通知策略创建成功"
    )


@router.get("/{reminder_id}/notification-config", response_model=ApiResponse[ReminderNotificationResponse])
async def get_notification_config(
    reminder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[ReminderNotificationResponse]:
    """获取提醒的通知策略"""
    # 检查提醒是否存在且有权限
    user_id = int(current_user.id)  
    reminder_repo = ReminderRepository(db)
    reminder = await reminder_repo.get_by_id(reminder_id, user_id)
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    # 获取配置
    notification_repo = ReminderNotificationRepository(db)
    config = await notification_repo.get_by_reminder_id(reminder_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该提醒尚未配置通知策略"
        )
    
    return ApiResponse[ReminderNotificationResponse].success(data=ReminderNotificationResponse.model_validate(config))


@router.put("/{reminder_id}/notification-config", response_model=ApiResponse[ReminderNotificationResponse])
async def update_notification_config(
    reminder_id: int,
    config: ReminderNotificationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[ReminderNotificationResponse]:
    """更新提醒的通知策略"""
    # 检查提醒权限
    user_id = int(current_user.id)  
    reminder_repo = ReminderRepository(db)
    reminder = await reminder_repo.get_by_id(reminder_id, user_id)
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    # 更新配置
    notification_repo = ReminderNotificationRepository(db)
    update_data = config.model_dump(exclude_unset=True)
    
    updated_config = await notification_repo.update(reminder_id, **update_data)
    
    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知策略不存在"
        )
    
    logger.info(
        "notification_config_updated",
        reminder_id=reminder_id,
        user_id=current_user.id,
        updated_fields=list(update_data.keys()),
        event="notification_config_update"
    )
    
    return ApiResponse[ReminderNotificationResponse].success(
        data=ReminderNotificationResponse.model_validate(updated_config),
        message="通知策略更新成功"
    )


@router.delete("/{reminder_id}/notification-config", response_model=ApiResponse[None])
async def delete_notification_config(
    reminder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[None]:
    """删除提醒的通知策略"""
    # 检查提醒权限
    user_id = int(current_user.id)  
    reminder_repo = ReminderRepository(db)
    reminder = await reminder_repo.get_by_id(reminder_id, user_id)
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    # 删除配置
    notification_repo = ReminderNotificationRepository(db)
    success = await notification_repo.delete(reminder_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知策略不存在"
        )
    
    logger.info(
        "notification_config_deleted",
        reminder_id=reminder_id,
        user_id=current_user.id,
        event="notification_config_delete"
    )
    
    return ApiResponse[None].success(message="通知策略已删除")


@router.get("/{reminder_id}/notification-schedule", response_model=ApiResponse[NotificationScheduleResponse])
async def get_notification_schedule(
    reminder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[NotificationScheduleResponse]:
    """
    获取提醒的通知时间表
    
    返回所有计划的通知时间，包括：
    - 提前通知时间列表
    - 当天通知时间列表
    - 总通知次数
    """
    # 检查提醒权限
    user_id = int(current_user.id)  
    reminder_repo = ReminderRepository(db)
    reminder = await reminder_repo.get_by_id(reminder_id, user_id)
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    # 获取通知配置
    notification_repo = ReminderNotificationRepository(db)
    config = await notification_repo.get_by_reminder_id(reminder_id)
    
    # 计算通知时间表
    notification_service = get_advanced_notification_service()
    
    advance_times = notification_service.calculate_advance_notification_times(reminder, config) if config else []
    same_day_times = notification_service.calculate_same_day_notification_times(reminder, config) if config else [reminder.first_remind_time]
    all_times = notification_service.get_all_notification_times(reminder, config)
    
    response = NotificationScheduleResponse(
        reminder_id=reminder.id, 
        reminder_title=reminder.title, 
        reminder_time=reminder.first_remind_time, 
        notification_times=all_times,
        advance_notifications=advance_times,
        same_day_notifications=same_day_times, 
        total_count=len(all_times)
    )
    
    logger.info(
        "notification_schedule_retrieved",
        reminder_id=reminder_id,
        total_notifications=len(all_times),
        advance_count=len(advance_times),
        same_day_count=len(same_day_times),
        event="schedule_query"
    )
    
    return ApiResponse[NotificationScheduleResponse].success(data=response)
