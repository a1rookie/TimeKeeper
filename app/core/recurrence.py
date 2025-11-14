"""
Recurrence Calculation Module
周期计算模块 - 计算下一次提醒时间
"""

from datetime import datetime, timedelta


def calculate_next_occurrence(
    current_time: datetime,
    recurrence_type: str,
    recurrence_config: dict
) -> datetime:
    """
    计算下一次提醒时间
    
    Args:
        current_time: 当前时间
        recurrence_type: 周期类型(字符串: "once", "daily", "weekly", "monthly", "yearly")
        recurrence_config: 周期配置
    
    Returns:
        下一次提醒时间
    """
    if recurrence_type == "once":
        # 一次性提醒，返回原时间
        return current_time
    
    elif recurrence_type == "daily":
        # 每日提醒
        interval = recurrence_config.get("interval", 1)
        return current_time + timedelta(days=interval)
    
    elif recurrence_type == "weekly":
        # 每周提醒
        interval = recurrence_config.get("interval", 1)
        return current_time + timedelta(weeks=interval)
    
    elif recurrence_type == "monthly":
        # 每月提醒（简化版，直接加30天）
        interval = recurrence_config.get("interval", 1)
        return current_time + timedelta(days=30 * interval)
    
    elif recurrence_type == "yearly":
        # 每年提醒（简化版，直接加365天）
        interval = recurrence_config.get("interval", 1)
        return current_time + timedelta(days=365 * interval)
    
    elif recurrence_type == "custom":
        # 自定义周期
        days = recurrence_config.get("days", 1)
        return current_time + timedelta(days=days)
    
    else:
        # 默认返回第二天
        return current_time + timedelta(days=1)
