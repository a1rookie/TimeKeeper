"""
Recurrence Calculation Module
周期计算模块 - 计算下一次提醒时间
"""

from datetime import datetime, timedelta
import calendar


def calculate_next_occurrence(
    current_time: datetime,
    recurrence_type: str,
    recurrence_config: dict
) -> datetime:
    """
    计算下一次提醒时间
    
    Args:
        current_time: 当前时间
        recurrence_type: 周期类型(字符串: "once", "daily", "weekly", "monthly", "yearly", "custom")
        recurrence_config: 周期配置
            - daily: {"interval": 1} - 间隔天数，默认1
            - weekly: {"interval": 1, "weekdays": [0,2,4]} - 间隔周数和指定星期几（0=周一，6=周日）
            - monthly: {"interval": 1, "day": 15} - 间隔月数和每月的第几天
            - yearly: {"interval": 1, "month": 6, "day": 15} - 间隔年数和月日
            - custom: {"days": 3} - 自定义间隔天数
    
    Returns:
        下一次提醒时间
        
    Examples:
        # 每天
        calculate_next_occurrence(datetime(2024, 1, 1, 10, 0), "daily", {})
        -> datetime(2024, 1, 2, 10, 0)
        
        # 每周一、三、五
        calculate_next_occurrence(datetime(2024, 1, 1, 10, 0), "weekly", {"weekdays": [0, 2, 4]})
        -> datetime(2024, 1, 3, 10, 0)  # 下一个符合条件的日期
        
        # 每月15号
        calculate_next_occurrence(datetime(2024, 1, 15, 10, 0), "monthly", {"day": 15})
        -> datetime(2024, 2, 15, 10, 0)
        
        # 每年6月15日
        calculate_next_occurrence(datetime(2024, 6, 15, 10, 0), "yearly", {"month": 6, "day": 15})
        -> datetime(2025, 6, 15, 10, 0)
    """
    if recurrence_type == "once":
        # 一次性提醒，返回原时间
        return current_time
    
    elif recurrence_type == "daily":
        # 每日提醒
        interval = recurrence_config.get("interval", 1)
        return current_time + timedelta(days=interval)
    
    elif recurrence_type == "weekly":
        # 每周提醒（支持指定星期几）
        interval = recurrence_config.get("interval", 1)
        weekdays = recurrence_config.get("weekdays", [])
        
        if not weekdays:
            # 如果没有指定星期，就按间隔周数计算
            return current_time + timedelta(weeks=interval)
        
        # 找到下一个符合条件的星期
        for days_ahead in range(1, 8):
            next_date = current_time + timedelta(days=days_ahead)
            if next_date.weekday() in weekdays:
                return next_date
        
        # 如果当前周没有符合的，跳到下一周
        weeks_to_add = interval
        next_date = current_time + timedelta(weeks=weeks_to_add)
        
        # 在下一周找第一个符合条件的日期
        for days_ahead in range(7):
            check_date = next_date + timedelta(days=days_ahead)
            if check_date.weekday() in weekdays:
                return check_date
        
        # 默认返回间隔周数后的同一天
        return current_time + timedelta(weeks=interval)
    
    elif recurrence_type == "monthly":
        # 每月提醒（支持指定每月的第几天）
        interval = recurrence_config.get("interval", 1)
        target_day = recurrence_config.get("day", current_time.day)
        
        # 计算下一个月
        year = current_time.year
        month = current_time.month + interval
        
        # 处理跨年
        while month > 12:
            month -= 12
            year += 1
        
        # 确保目标日期在该月有效（处理2月29/30/31日的情况）
        max_day = calendar.monthrange(year, month)[1]
        day = min(target_day, max_day)
        
        try:
            return current_time.replace(year=year, month=month, day=day)
        except ValueError:
            # 如果日期无效，使用该月最后一天
            return current_time.replace(year=year, month=month, day=max_day)
    
    elif recurrence_type == "yearly":
        # 每年提醒（支持指定月日）
        interval = recurrence_config.get("interval", 1)
        target_month = recurrence_config.get("month", current_time.month)
        target_day = recurrence_config.get("day", current_time.day)
        
        year = current_time.year + interval
        
        # 处理闰年2月29日的情况
        if target_month == 2 and target_day == 29:
            if not calendar.isleap(year):
                target_day = 28
        
        try:
            return current_time.replace(year=year, month=target_month, day=target_day)
        except ValueError:
            # 如果日期无效，使用该月最后一天
            max_day = calendar.monthrange(year, target_month)[1]
            return current_time.replace(year=year, month=target_month, day=max_day)
    
    elif recurrence_type == "custom":
        # 自定义周期
        days = recurrence_config.get("days", 1)
        return current_time + timedelta(days=days)
    
    else:
        # 默认返回第二天
        return current_time + timedelta(days=1)
