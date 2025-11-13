"""
Push Log Repository
推送日志数据访问层
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import and_, desc
from app.models.push_log import PushLog, PushStatus, UserAction


class PushLogRepository:
    """推送日志数据访问"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        push_task_id: int,
        channel: str,
        status: PushStatus,
        request_data: Optional[dict] = None,
        response_data: Optional[dict] = None,
        error_message: Optional[str] = None,
        user_action: Optional[UserAction] = None,
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
    
    async def get_by_id(self, log_id: int) -> Optional[PushLog]:
        """根据ID查询日志"""
        result = await self.db.execute(select(PushLog).filter(PushLog.id == log_id))
        return result.scalar_one_or_none()
    
    async def get_by_task(self, push_task_id: int) -> List[PushLog]:
        """查询推送任务的所有日志"""
        return self.db.query(PushLog).filter(
            PushLog.push_task_id == push_task_id
        ).order_by(PushLog.created_at).all()
    
    async def get_failed_logs(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[PushLog]:
        """查询失败的推送日志"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(PushLog).filter(
            and_(
                PushLog.status == PushStatus.FAILED,
                PushLog.created_at >= since
            )
        ).order_by(desc(PushLog.created_at)).limit(limit).all()
    
    async def get_channel_stats(self, channel: str, days: int = 7) -> dict:
        """统计渠道推送效果"""
        since = datetime.utcnow() - timedelta(days=days)
        
        total = self.db.query(PushLog).filter(
            and_(
                PushLog.channel == channel,
                PushLog.created_at >= since
            )
        ).count()
        
        success = self.db.query(PushLog).filter(
            and_(
                PushLog.channel == channel,
                PushLog.status == PushStatus.SUCCESS,
                PushLog.created_at >= since
            )
        ).count()
        
        failed = self.db.query(PushLog).filter(
            and_(
                PushLog.channel == channel,
                PushLog.status == PushStatus.FAILED,
                PushLog.created_at >= since
            )
        ).count()
        
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
        user_action: UserAction,
        response_time_seconds: int
    ) -> Optional[PushLog]:
        """更新用户响应动作"""
        log = self.get_by_id(log_id)
        if not log:
            return None
        
        log.user_action = user_action
        log.response_time_seconds = response_time_seconds
        await self.db.commit()
        await self.db.refresh(log)
        return log
