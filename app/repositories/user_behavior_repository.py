"""
User Behavior Repository
用户行为数据访问层
"""
from typing import List, Optional
from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import and_
from app.models.user_behavior import UserBehavior


class UserBehaviorRepository:
    """用户行为数据访问"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_or_update(
        self,
        user_id: int,
        behavior_date: date,
        active_hours: Optional[List[int]] = None,
        reminder_count: int = 0,
        completion_count: int = 0,
        completion_rate: Decimal = Decimal("0.0"),
        avg_response_time_seconds: Optional[int] = None,
        voice_input_count: int = 0,
        template_usage_count: int = 0
    ) -> UserBehavior:
        """创建或更新用户行为数据"""
        stmt = select(UserBehavior).where(
            and_(
                UserBehavior.user_id == user_id,
                UserBehavior.behavior_date == behavior_date
            )
        )
        result = await self.db.execute(stmt)
        behavior = result.scalar_one_or_none()
        
        if behavior:
            # 更新
            behavior.active_hours = active_hours
            behavior.reminder_count = reminder_count
            behavior.completion_count = completion_count
            behavior.completion_rate = completion_rate
            behavior.avg_response_time_seconds = avg_response_time_seconds
            behavior.voice_input_count = voice_input_count
            behavior.template_usage_count = template_usage_count
        else:
            # 创建
            behavior = UserBehavior(
                user_id=user_id,
                behavior_date=behavior_date,
                active_hours=active_hours,
                reminder_count=reminder_count,
                completion_count=completion_count,
                completion_rate=completion_rate,
                avg_response_time_seconds=avg_response_time_seconds,
                voice_input_count=voice_input_count,
                template_usage_count=template_usage_count
            )
            self.db.add(behavior)
        
        await self.db.commit()
        await self.db.refresh(behavior)
        return behavior
    
    async def get_by_date(self, user_id: int, behavior_date: date) -> UserBehavior | None:
        """查询指定日期的行为数据"""
        stmt = select(UserBehavior).where(
            and_(
                UserBehavior.user_id == user_id,
                UserBehavior.behavior_date == behavior_date
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_date_range(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> Sequence[UserBehavior]:
        """查询日期范围内的行为数据"""
        stmt = select(UserBehavior).where(
            and_(
                UserBehavior.user_id == user_id,
                UserBehavior.behavior_date >= start_date,
                UserBehavior.behavior_date <= end_date
            )
        ).order_by(UserBehavior.behavior_date)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_recent(self, user_id: int, days: int = 30) -> Sequence[UserBehavior]:
        """查询最近N天的行为数据"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        return await self.get_date_range(user_id, start_date, end_date)
    
    async def calculate_avg_completion_rate(self, user_id: int, days: int = 30) -> float:
        """计算平均完成率"""
        behaviors = await self.get_recent(user_id, days)
        if not behaviors:
            return 0.0
        
        total_rate = sum(float(b.completion_rate) for b in behaviors if b.completion_rate is not None)
        return round(total_rate / len(behaviors), 2)
    
    async def get_most_active_hours(self, user_id: int, days: int = 30) -> List[int]:
        """获取最活跃的时间段"""
        behaviors = await self.get_recent(user_id, days)
        if not behaviors:
            return []
        
        # 统计各小时的活跃次数
        hour_counts: dict[int, int] = {}
        for behavior in behaviors:
            if behavior.active_hours:
                # active_hours 是 List[int]，表示活跃的小时列表
                for hour in behavior.active_hours:
                    hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        # 排序并返回前5个最活跃时段
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:5]]
