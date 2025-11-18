"""
SMS Log Repository
短信日志数据访问层
"""
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import func
from app.models.sms_log import SmsLog


class SmsLogRepository:
    """短信日志 Repository"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        phone: str,
        purpose: str,
        code: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        provider: str = "noop",
        expires_at: datetime | None = None
    ) -> SmsLog:
        """创建短信日志"""
        log = SmsLog(
            phone=phone,
            purpose=purpose,
            code=code,  # 注意：生产环境应加密或脱敏
            ip_address=ip_address,
            user_agent=user_agent,
            provider=provider,
            status="pending",
            expires_at=expires_at
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log
    
    async def update_status(self, log_id: int, status: str, error_message: str | None = None):
        """更新发送状态"""
        from sqlalchemy import update as sql_update
        now = datetime.now()
        update_data = {"status": status, "sent_at": now}
        if error_message:
            update_data["error_message"] = error_message
        
        stmt = sql_update(SmsLog).where(SmsLog.id == log_id).values(**update_data)
        await self.db.execute(stmt)
        await self.db.commit()
    
    async def mark_verified(self, log_id: int):
        """标记为已验证"""
        from sqlalchemy import update as sql_update
        now = datetime.now()
        stmt = sql_update(SmsLog).where(SmsLog.id == log_id).values(
            is_verified=True,
            verified_at=now
        )
        await self.db.execute(stmt)
        await self.db.commit()
    
    async def increment_verify_attempts(self, phone: str, purpose: str) -> int:
        """增加验证尝试次数（返回最新的未过期记录的尝试次数）"""
        from sqlalchemy import update as sql_update
        now = datetime.now()
        stmt = select(SmsLog).where(
            SmsLog.phone == phone,
            SmsLog.purpose == purpose,
            SmsLog.is_verified == False,
            SmsLog.expires_at > now
        ).order_by(SmsLog.created_at.desc()).limit(1)
        result = await self.db.execute(stmt)
        log = result.scalar_one_or_none()
        
        if log:
            log_id = int(log.id)
            update_stmt = sql_update(SmsLog).where(SmsLog.id == log_id).values(
                verify_attempts=SmsLog.verify_attempts + 1
            )
            await self.db.execute(update_stmt)
            await self.db.commit()
            # 重新查询以获取更新后的值
            result = await self.db.execute(select(SmsLog).where(SmsLog.id == log_id))
            updated_log = result.scalar_one_or_none()
            return int(updated_log.verify_attempts) if updated_log else 0
        return 0
    
    async def count_by_phone_today(self, phone: str, purpose: str | None = None) -> int:
        """统计手机号今日发送次数"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(func.count()).select_from(SmsLog).where(
            SmsLog.phone == phone,
            SmsLog.created_at >= today_start
        )
        if purpose:
            stmt = stmt.where(SmsLog.purpose == purpose)
        result = await self.db.execute(stmt)
        return result.scalar() or 0
    
    async def count_by_ip_today(self, ip_address: str) -> int:
        """统计IP今日发送次数"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(func.count()).select_from(SmsLog).where(
            SmsLog.ip_address == ip_address,
            SmsLog.created_at >= today_start
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
    
    async def count_recent(self, phone: str, purpose: str, minutes: int = 1) -> int:
        """统计最近N分钟内的发送次数"""
        time_threshold = datetime.now() - timedelta(minutes=minutes)
        stmt = select(func.count()).select_from(SmsLog).where(
            SmsLog.phone == phone,
            SmsLog.purpose == purpose,
            SmsLog.created_at >= time_threshold
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
    
    async def get_latest_unverified(self, phone: str, purpose: str) -> SmsLog | None:
        """获取最新的未验证记录"""
        now = datetime.now()
        stmt = select(SmsLog).where(
            SmsLog.phone == phone,
            SmsLog.purpose == purpose,
            SmsLog.is_verified == False,
            SmsLog.expires_at > now
        ).order_by(SmsLog.created_at.desc()).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def cleanup_expired(self, days: int = 30):
        """清理过期日志（保留30天）"""
        from sqlalchemy import delete
        threshold = datetime.now() - timedelta(days=days)
        stmt = delete(SmsLog).where(SmsLog.created_at < threshold)
        await self.db.execute(stmt)
        await self.db.commit()
