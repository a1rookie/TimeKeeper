"""
Push Log Repository
推送日志数据访问层
"""
from collections.abc import Sequence
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import and_, desc
from app.models.push_log import PushLog


class PushLogRepository:
    """推送日志数据访问"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        push_task_id: int,
        channel: str,
        status: str,
        request_data: Optional[dict] = None,
        response_data: Optional[dict] = None,
        error_message: Optional[str] = None,
        user_action: Optional[str] = None,
        response_time_seconds: Optional[int] = None
    ) -> PushLog:
        """创建推送日志"""
        log = PushLog(
            push_task_id=push_task_id,
            channel=channel,
            status=status,
            request_data=request_data,
            response_data=response_data,
            error_message=error_message,
            user_action=user_action,
            response_time_seconds=response_time_seconds
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log
    
    async def get_by_id(self, log_id: int) -> PushLog | None:
        """根据ID查询日志"""
        result = await self.db.execute(select(PushLog).filter(PushLog.id == log_id))
        return result.scalar_one_or_none()
    
    async def get_by_task(self, push_task_id: int) -> Sequence[PushLog]:
        """查询推送任务的所有日志"""
        stmt = select(PushLog).where(
            PushLog.push_task_id == push_task_id
        ).order_by(PushLog.created_at)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_failed_logs(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> Sequence[PushLog]:
        """查询失败的推送日志"""
        since = datetime.utcnow() - timedelta(hours=hours)
        stmt = select(PushLog).where(
            and_(
                PushLog.status == "failed",
                PushLog.created_at >= since
            )
        ).order_by(desc(PushLog.created_at)).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_channel_stats(self, channel: str, days: int = 7) -> dict:
        """统计渠道推送效果"""
        from sqlalchemy import func
        since = datetime.utcnow() - timedelta(days=days)
        
        # 统计总数
        stmt_total = select(func.count()).select_from(PushLog).where(
            and_(
                PushLog.channel == channel,
                PushLog.created_at >= since
            )
        )
        result_total = await self.db.execute(stmt_total)
        total = result_total.scalar() or 0
        
        # 统计成功数
        stmt_success = select(func.count()).select_from(PushLog).where(
            and_(
                PushLog.channel == channel,
                PushLog.status == "success",
                PushLog.created_at >= since
            )
        )
        result_success = await self.db.execute(stmt_success)
        success = result_success.scalar() or 0
        
        # 统计失败数
        stmt_failed = select(func.count()).select_from(PushLog).where(
            and_(
                PushLog.channel == channel,
                PushLog.status == "failed",
                PushLog.created_at >= since
            )
        )
        result_failed = await self.db.execute(stmt_failed)
        failed = result_failed.scalar() or 0
        
        return {
            "channel": channel,
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": round(success / total * 100, 2) if total > 0 else 0
        }
    
    async def update_user_action(
        self,
        log_id: int,
        user_action: str,
        response_time_seconds: int
    ) -> PushLog | None:
        """更新用户响应动作"""
        log = await self.get_by_id(log_id)
        if not log:
            return None
        
        log.user_action = user_action
        log.response_time_seconds = response_time_seconds
        await self.db.commit()
        await self.db.refresh(log)
        return log
