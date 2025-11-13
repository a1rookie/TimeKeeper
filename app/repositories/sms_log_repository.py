"""
SMS Log Repository
短信日志数据访问层
"""
from typing import Optional, List
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
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        provider: str = "noop",
        expires_at: Optional[datetime] = None
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
    
    async def update_status(self, log_id: int, status: str, error_message: Optional[str] = None):
        """更新发送状态"""
        log = self.db.query(SmsLog).filter(SmsLog.id == log_id).first()
        if log:
            log.status = status
            log.sent_at = func.now()
            if error_message:
                log.error_message = error_message
            await self.db.commit()
    
    async def mark_verified(self, log_id: int):
        """标记为已验证"""
        log = self.db.query(SmsLog).filter(SmsLog.id == log_id).first()
        if log:
            log.is_verified = True
            log.verified_at = func.now()
            await self.db.commit()
    
    async def increment_verify_attempts(self, phone: str, purpose: str) -> int:
        """增加验证尝试次数（返回最新的未过期记录的尝试次数）"""
        log = self.db.query(SmsLog).filter(
            SmsLog.phone == phone,
            SmsLog.purpose == purpose,
            SmsLog.is_verified == False,
            SmsLog.expires_at > func.now()
        ).order_by(SmsLog.created_at.desc()).first()
        
        if log:
            log.verify_attempts += 1
            await self.db.commit()
            return log.verify_attempts
        return 0
    
    async def count_by_phone_today(self, phone: str, purpose: Optional[str] = None) -> int:
        """统计手机号今日发送次数"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        query = self.db.query(SmsLog).filter(
            SmsLog.phone == phone,
            SmsLog.created_at >= today_start
        )
        if purpose:
            query = query.filter(SmsLog.purpose == purpose)
        return query.count()
    
    async def count_by_ip_today(self, ip_address: str) -> int:
        """统计IP今日发送次数"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.db.query(SmsLog).filter(
            SmsLog.ip_address == ip_address,
            SmsLog.created_at >= today_start
        ).count()
    
    async def count_recent(self, phone: str, purpose: str, minutes: int = 1) -> int:
        """统计最近N分钟内的发送次数"""
        time_threshold = datetime.now() - timedelta(minutes=minutes)
        return self.db.query(SmsLog).filter(
            SmsLog.phone == phone,
            SmsLog.purpose == purpose,
            SmsLog.created_at >= time_threshold
        ).count()
    
    async def get_latest_unverified(self, phone: str, purpose: str) -> Optional[SmsLog]:
        """获取最新的未验证记录"""
        return self.db.query(SmsLog).filter(
            SmsLog.phone == phone,
            SmsLog.purpose == purpose,
            SmsLog.is_verified == False,
            SmsLog.expires_at > func.now()
        ).order_by(SmsLog.created_at.desc()).first()
    
    async def cleanup_expired(self, days: int = 30):
        """清理过期日志（保留30天）"""
        threshold = datetime.now() - timedelta(days=days)
        self.db.query(SmsLog).filter(SmsLog.created_at < threshold).delete()
        await self.db.commit()
