"""
Advanced Reminder Notification Service
高级提醒通知服务 - 处理复杂的通知策略
"""
from typing import List, Optional
from datetime import datetime, timedelta, time
import structlog

from app.models.reminder_notification import ReminderNotification
from app.models.reminder import Reminder

logger = structlog.get_logger(__name__)


class AdvancedNotificationService:
    """高级通知服务"""
    
    # 夜间时间定义（22:00 - 07:00）
    NIGHT_START_HOUR = 22
    NIGHT_END_HOUR = 7
    
    @staticmethod
    def is_night_time(check_time: time) -> bool:
        """判断是否为夜间时间"""
        hour = check_time.hour
        return hour >= AdvancedNotificationService.NIGHT_START_HOUR or hour < AdvancedNotificationService.NIGHT_END_HOUR
    
    @staticmethod
    def adjust_time_if_night(
        target_time: time,
        avoid_night: bool = True,
        fallback_time: str = "09:00"
    ) -> time:
        """
        如果是夜间时间，调整到白天时间
        
        Args:
            target_time: 目标时间
            avoid_night: 是否避免夜间
            fallback_time: 回退时间（HH:MM格式）
            
        Returns:
            调整后的时间
        """
        if not avoid_night:
            return target_time
        
        if AdvancedNotificationService.is_night_time(target_time):
            # 转换回退时间
            hour, minute = map(int, fallback_time.split(':'))
            adjusted_time = time(hour=hour, minute=minute)
            
            logger.info(
                "night_time_adjusted",
                original_time=target_time.strftime("%H:%M"),
                adjusted_time=adjusted_time.strftime("%H:%M"),
                event="time_adjustment"
            )
            
            return adjusted_time
        
        return target_time
    
    @staticmethod
    def calculate_advance_notification_times(
        reminder: Reminder,
        notification_config: ReminderNotification
    ) -> List[datetime]:
        """
        计算提前通知时间列表
        
        例如：生日在 2025-03-08，提前5天，每2天通知一次，时间09:00
        返回：[2025-03-03 09:00, 2025-03-05 09:00, 2025-03-07 09:00]
        
        Args:
            reminder: 提醒对象
            notification_config: 通知配置
            
        Returns:
            提前通知时间列表
        """
        if not notification_config.advance_notify_enabled or notification_config.advance_days <= 0:
            return []
        
        result = []
        base_datetime = reminder.first_remind_time
        advance_days = notification_config.advance_days
        interval = notification_config.advance_notify_interval
        
        # 解析通知时间
        hour, minute = map(int, notification_config.advance_notify_time.split(':'))
        notify_time = time(hour=hour, minute=minute)
        
        # 智能时间调整
        notify_time = AdvancedNotificationService.adjust_time_if_night(
            notify_time,
            notification_config.avoid_night_time,
            notification_config.night_time_fallback
        )
        
        # 计算提前通知日期
        current_advance = advance_days
        while current_advance > 0:
            notify_date = base_datetime.date() - timedelta(days=current_advance)
            notify_datetime = datetime.combine(notify_date, notify_time)
            
            # 只添加未来的时间
            if notify_datetime > datetime.now():
                result.append(notify_datetime)
            
            current_advance -= interval
        
        logger.info(
            "advance_notifications_calculated",
            reminder_id=reminder.id,
            advance_days=advance_days,
            interval=interval,
            notification_count=len(result),
            event="advance_calculation"
        )
        
        return sorted(result)
    
    @staticmethod
    def calculate_same_day_notification_times(
        reminder: Reminder,
        notification_config: ReminderNotification
    ) -> List[datetime]:
        """
        计算当天通知时间列表
        
        例如：提醒时间 2025-03-08 20:00，当天通知 ["08:00", "12:00", "20:00"]
        返回：[2025-03-08 08:00, 2025-03-08 12:00, 2025-03-08 20:00]
        
        Args:
            reminder: 提醒对象
            notification_config: 通知配置
            
        Returns:
            当天通知时间列表
        """
        if not notification_config.same_day_notifications:
            # 如果没有配置当天通知，返回提醒本身的时间
            return [reminder.first_remind_time]
        
        result = []
        remind_date = reminder.first_remind_time.date()
        
        for time_str in notification_config.same_day_notifications:
            try:
                hour, minute = map(int, time_str.split(':'))
                notify_time = time(hour=hour, minute=minute)
                
                # 智能时间调整
                notify_time = AdvancedNotificationService.adjust_time_if_night(
                    notify_time,
                    notification_config.avoid_night_time,
                    notification_config.night_time_fallback
                )
                
                notify_datetime = datetime.combine(remind_date, notify_time)
                
                # 只添加未来的时间
                if notify_datetime > datetime.now():
                    result.append(notify_datetime)
                    
            except ValueError as e:
                logger.error(
                    "invalid_time_format",
                    time_str=time_str,
                    error=str(e),
                    event="time_parse_error"
                )
        
        logger.info(
            "same_day_notifications_calculated",
            reminder_id=reminder.id,
            configured_times=len(notification_config.same_day_notifications),
            valid_times=len(result),
            event="same_day_calculation"
        )
        
        return sorted(result)
    
    @staticmethod
    def get_all_notification_times(
        reminder: Reminder,
        notification_config: Optional[ReminderNotification]
    ) -> List[datetime]:
        """
        获取所有通知时间（提前通知 + 当天通知）
        
        Args:
            reminder: 提醒对象
            notification_config: 通知配置（可选）
            
        Returns:
            所有通知时间列表（已排序）
        """
        if not notification_config or not notification_config.is_active:
            # 没有配置或未启用，返回默认提醒时间
            return [reminder.first_remind_time]
        
        all_times = []
        
        # 1. 提前通知
        advance_times = AdvancedNotificationService.calculate_advance_notification_times(
            reminder, notification_config
        )
        all_times.extend(advance_times)
        
        # 2. 当天通知
        same_day_times = AdvancedNotificationService.calculate_same_day_notification_times(
            reminder, notification_config
        )
        all_times.extend(same_day_times)
        
        # 去重并排序
        all_times = sorted(list(set(all_times)))
        
        logger.info(
            "all_notifications_calculated",
            reminder_id=reminder.id,
            advance_count=len(advance_times),
            same_day_count=len(same_day_times),
            total_count=len(all_times),
            event="notification_schedule_complete"
        )
        
        return all_times
    
    @staticmethod
    def generate_notification_message(
        reminder: Reminder,
        notification_config: Optional[ReminderNotification],
        notification_time: datetime
    ) -> str:
        """
        生成通知消息
        
        Args:
            reminder: 提醒对象
            notification_config: 通知配置
            notification_time: 通知时间
            
        Returns:
            通知消息文本
        """
        # 使用自定义模板
        if notification_config and notification_config.custom_message_template:
            template = notification_config.custom_message_template
            # 简单的变量替换
            message = template.replace("{title}", reminder.title)
            message = message.replace("{time}", notification_time.strftime("%Y-%m-%d %H:%M"))
            return message
        
        # 计算时间差
        time_diff = reminder.first_remind_time - notification_time
        days_before = time_diff.days
        
        # 生成默认消息
        if days_before > 0:
            return f"【提前通知】{reminder.title} 还有 {days_before} 天（{reminder.first_remind_time.strftime('%m月%d日 %H:%M')}）"
        elif days_before == 0:
            # 同一天
            hours_diff = time_diff.seconds // 3600
            if hours_diff > 0:
                return f"【提前提醒】{reminder.title} 将在 {hours_diff} 小时后（{reminder.first_remind_time.strftime('%H:%M')}）"
            else:
                return f"【准时提醒】{reminder.title}"
        else:
            return f"【提醒】{reminder.title}"


def get_advanced_notification_service() -> AdvancedNotificationService:
    """获取高级通知服务实例"""
    return AdvancedNotificationService()
