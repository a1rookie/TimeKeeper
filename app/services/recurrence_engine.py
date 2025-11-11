"""
Recurrence Engine Service
周期计算引擎服务
"""

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app.models.reminder import RecurrenceType


class RecurrenceEngine:
    """
    周期计算引擎
    负责计算各种周期类型的下次提醒时间
    """
    
    @staticmethod
    def calculate_next_time(
        recurrence_type: RecurrenceType,
        config: dict,
        last_time: datetime
    ) -> datetime:
        """
        Calculate next reminder time based on recurrence type
        根据周期类型计算下次提醒时间
        
        Args:
            recurrence_type: 周期类型
            config: 周期配置
            last_time: 上次提醒时间
            
        Returns:
            下次提醒时间
        """
        if recurrence_type == RecurrenceType.DAILY:
            return RecurrenceEngine._calculate_daily(config, last_time)
        
        elif recurrence_type == RecurrenceType.WEEKLY:
            return RecurrenceEngine._calculate_weekly(config, last_time)
        
        elif recurrence_type == RecurrenceType.MONTHLY:
            return RecurrenceEngine._calculate_monthly(config, last_time)
        
        elif recurrence_type == RecurrenceType.YEARLY:
            return RecurrenceEngine._calculate_yearly(config, last_time)
        
        else:
            # Custom recurrence - handle special cases
            return RecurrenceEngine._calculate_custom(config, last_time)
    
    @staticmethod
    def _calculate_daily(config: dict, last_time: datetime) -> datetime:
        """
        Calculate next time for daily recurrence
        计算每日周期
        
        Config example: {"interval": 1}  # Every N days
        """
        interval = config.get("interval", 1)
        return last_time + timedelta(days=interval)
    
    @staticmethod
    def _calculate_weekly(config: dict, last_time: datetime) -> datetime:
        """
        Calculate next time for weekly recurrence
        计算每周周期
        
        Config example: {"weekdays": [1, 3, 5]}  # Monday, Wednesday, Friday
        """
        weekdays = config.get("weekdays", [last_time.weekday()])
        weekdays = sorted(weekdays)
        
        current_weekday = last_time.weekday()
        
        # Find next weekday
        for weekday in weekdays:
            if weekday > current_weekday:
                days_ahead = weekday - current_weekday
                return last_time + timedelta(days=days_ahead)
        
        # If no weekday found in current week, go to first weekday of next week
        days_ahead = (7 - current_weekday) + weekdays[0]
        return last_time + timedelta(days=days_ahead)
    
    @staticmethod
    def _calculate_monthly(config: dict, last_time: datetime) -> datetime:
        """
        Calculate next time for monthly recurrence
        计算每月周期
        
        Config example: 
        - {"day_of_month": 25}  # 25th of each month
        - {"day_of_month": -1}  # Last day of month
        - {"skip_weekend": true}  # Skip to next weekday if falls on weekend
        
        边界情况处理:
        - 月末日期 (如1月31日): 在2月会回退到2月28/29日
        - 闰年处理: 2月29日在非闰年会回退到2月28日
        - 跨年: 12月自动进入下一年1月
        """
        # Support both "day" and "day_of_month" for backward compatibility
        target_day = config.get("day_of_month") or config.get("day", last_time.day)
        skip_weekend = config.get("skip_weekend", False)
        interval = config.get("interval", 1)  # Support N-month intervals
        
        # Calculate next month
        next_time = last_time + relativedelta(months=interval)
        
        # Handle special days
        if target_day == -1:
            # Last day of month - always use the actual last day
            next_time = next_time + relativedelta(day=31)
        else:
            # Try to use target day, fall back to last day of month if invalid
            try:
                next_time = next_time.replace(day=target_day)
            except ValueError:
                # Day doesn't exist in month (e.g., Feb 30, Feb 31)
                # Use the last valid day of that month
                next_time = next_time + relativedelta(day=31)
        
        # Skip weekend if needed
        if skip_weekend:
            if next_time.weekday() == 5:  # Saturday
                next_time += timedelta(days=2)
            elif next_time.weekday() == 6:  # Sunday
                next_time += timedelta(days=1)
        
        return next_time
    
    @staticmethod
    def _calculate_yearly(config: dict, last_time: datetime) -> datetime:
        """
        Calculate next time for yearly recurrence
        计算每年周期
        
        Config example: {"month": 3, "day": 15}  # March 15th each year
        
        边界情况处理:
        - 闰年生日 (2月29日): 在非闰年会回退到2月28日
        - 支持多年间隔: {"interval": 2} 表示每2年
        """
        target_month = config.get("month", last_time.month)
        target_day = config.get("day", last_time.day)
        interval = config.get("interval", 1)  # Support N-year intervals
        
        next_time = last_time + relativedelta(years=interval)
        
        try:
            next_time = next_time.replace(month=target_month, day=target_day)
        except ValueError:
            # Invalid date (e.g., Feb 29 in non-leap year)
            # Use Feb 28 instead
            if target_month == 2 and target_day == 29:
                next_time = next_time.replace(month=2, day=28)
            else:
                # Other invalid dates, use last day of target month
                next_time = next_time.replace(month=target_month)
                next_time = next_time + relativedelta(day=31)
        
        return next_time
    
    @staticmethod
    def _calculate_custom(config: dict, last_time: datetime) -> datetime:
        """
        Calculate next time for custom recurrence
        计算自定义周期
        
        Config example: {"days": 45}  # Every 45 days
        """
        days = config.get("days", 1)
        return last_time + timedelta(days=days)
