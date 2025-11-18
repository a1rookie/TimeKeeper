"""
Recurrence Service
周期计算服务 - 计算提醒的下次触发时间
"""
from datetime import datetime, timedelta
from typing import Dict, Any
import calendar


class RecurrenceService:
    """周期计算服务"""
    
    def calculate_next_time(
        self,
        recurrence_type: str,
        recurrence_config: Dict[str, Any],
        current_time: datetime
    ) -> datetime | None:
        """
        计算下次提醒时间
        
        Args:
            recurrence_type: 周期类型 (daily/weekly/monthly/yearly/custom/once)
            recurrence_config: 周期配置
            current_time: 当前时间
            
        Returns:
            下次提醒时间，如果是一次性提醒则返回None
        """
        if recurrence_type == "once":
            return None
        
        if recurrence_type == "daily":
            return self._calculate_daily(current_time, recurrence_config)
        elif recurrence_type == "weekly":
            return self._calculate_weekly(current_time, recurrence_config)
        elif recurrence_type == "monthly":
            return self._calculate_monthly(current_time, recurrence_config)
        elif recurrence_type == "yearly":
            return self._calculate_yearly(current_time, recurrence_config)
        elif recurrence_type == "custom":
            return self._calculate_custom(current_time, recurrence_config)
        
        return None
    
    def _calculate_daily(self, current_time: datetime, config: Dict) -> datetime:
        """计算每日周期"""
        # 默认加1天
        interval_days = config.get("interval_days", 1)
        next_time = current_time + timedelta(days=interval_days)
        
        # 如果配置了固定时间，设置时间
        if "time" in config:
            time_str = config["time"]  # 格式: "HH:MM"
            hour, minute = map(int, time_str.split(":"))
            next_time = next_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return next_time
    
    def _calculate_weekly(self, current_time: datetime, config: Dict) -> datetime:
        """计算每周周期"""
        # weekdays: [0, 1, 2, 3, 4, 5, 6] (周一到周日)
        weekdays = config.get("weekdays", [current_time.weekday()])
        weekdays = sorted(weekdays)
        
        # 当前星期几
        current_weekday = current_time.weekday()
        
        # 找到下一个符合的weekday
        next_weekday = None
        for wd in weekdays:
            if wd > current_weekday:
                next_weekday = wd
                break
        
        # 如果本周没有了，找下周的第一个
        if next_weekday is None:
            next_weekday = weekdays[0]
            days_ahead = (7 - current_weekday) + next_weekday
        else:
            days_ahead = next_weekday - current_weekday
        
        next_time = current_time + timedelta(days=days_ahead)
        
        # 设置时间
        if "time" in config:
            time_str = config["time"]
            hour, minute = map(int, time_str.split(":"))
            next_time = next_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return next_time
    
    def _calculate_monthly(self, current_time: datetime, config: Dict) -> datetime:
        """计算每月周期"""
        day = config.get("day", current_time.day)
        
        # 计算下个月
        next_month = current_time.month + 1
        next_year = current_time.year
        
        if next_month > 12:
            next_month = 1
            next_year += 1
        
        # 处理月末日期（如31号在2月不存在）
        max_day = calendar.monthrange(next_year, next_month)[1]
        actual_day = min(day, max_day)
        
        next_time = current_time.replace(
            year=next_year,
            month=next_month,
            day=actual_day
        )
        
        # 设置时间
        if "time" in config:
            time_str = config["time"]
            hour, minute = map(int, time_str.split(":"))
            next_time = next_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return next_time
    
    def _calculate_yearly(self, current_time: datetime, config: Dict) -> datetime:
        """计算每年周期"""
        month = config.get("month", current_time.month)
        day = config.get("day", current_time.day)
        
        next_year = current_time.year + 1
        
        # 处理闰年2月29日
        if month == 2 and day == 29:
            if not calendar.isleap(next_year):
                day = 28
        
        next_time = current_time.replace(
            year=next_year,
            month=month,
            day=day
        )
        
        # 设置时间
        if "time" in config:
            time_str = config["time"]
            hour, minute = map(int, time_str.split(":"))
            next_time = next_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return next_time
    
    def _calculate_custom(self, current_time: datetime, config: Dict) -> datetime:
        """计算自定义周期"""
        # 支持按天/周/月/年的自定义间隔
        days = config.get("days")
        weeks = config.get("weeks")
        months = config.get("months")
        years = config.get("years")
        
        if days:
            return current_time + timedelta(days=days)
        elif weeks:
            return current_time + timedelta(weeks=weeks)
        elif months:
            # 月份计算
            next_month = current_time.month + months
            next_year = current_time.year
            
            while next_month > 12:
                next_month -= 12
                next_year += 1
            
            max_day = calendar.monthrange(next_year, next_month)[1]
            actual_day = min(current_time.day, max_day)
            
            return current_time.replace(
                year=next_year,
                month=next_month,
                day=actual_day
            )
        elif years:
            return current_time.replace(year=current_time.year + years)
        
        # 默认加1天
        return current_time + timedelta(days=1)
