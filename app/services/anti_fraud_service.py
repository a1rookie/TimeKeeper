"""
Anti-Fraud Service
注册防刷服务 - 防止恶意注册和批量注册

防刷策略：
1. IP限制：同一IP每天最多注册N个账号
2. 时间限制：同一IP短时间内不能频繁注册
3. 短信验证码限制（已在sms_service实现）
4. 设备指纹检测（可选，需前端配合）
5. 黑名单机制
"""
from __future__ import annotations
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.config import settings
from app.core.redis import get_redis
from app.repositories.user_repository import UserRepository

logger = structlog.get_logger(__name__)


class AntiFraudService:
    """注册防刷服务"""
    
    # 限制配置（可通过环境变量配置）
    MAX_REGISTRATIONS_PER_IP_PER_DAY = 5  # 每个IP每天最多注册5个
    REGISTRATION_INTERVAL_SECONDS = 300  # 同一IP两次注册间隔至少5分钟
    IP_BLACKLIST_PREFIX = "ip_blacklist:"
    IP_REGISTRATION_COUNTER_PREFIX = "ip_reg_count:"
    IP_LAST_REGISTRATION_PREFIX = "ip_last_reg:"
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis = get_redis()
        self.user_repo = UserRepository(db)
    
    async def check_ip_registration_limit(self, ip_address: str) -> tuple[bool, str]:
        """
        检查IP注册限制
        
        Returns:
            (is_allowed, error_message)
        """
        if not ip_address:
            return True, ""
        
        # 1. 检查IP黑名单
        if await self.is_ip_blacklisted(ip_address):
            logger.warning("ip_blacklisted_registration_attempt", ip=ip_address)
            return False, "该IP地址已被封禁，如有疑问请联系客服"
        
        # 2. 检查每日注册次数（使用Repository）
        count_today = await self.user_repo.count_registrations_by_ip_today(ip_address)
        
        if count_today >= self.MAX_REGISTRATIONS_PER_IP_PER_DAY:
            logger.warning(
                "ip_daily_registration_limit_exceeded",
                ip=ip_address,
                count=count_today
            )
            return False, f"该IP今日注册次数已达上限({self.MAX_REGISTRATIONS_PER_IP_PER_DAY}次)"
        
        # 3. 检查注册时间间隔（使用Redis）
        if self.redis:
            last_reg_key = f"{self.IP_LAST_REGISTRATION_PREFIX}{ip_address}"
            last_reg_time = self.redis.get(last_reg_key)
            
            if last_reg_time:
                elapsed = datetime.now().timestamp() - float(last_reg_time)
                if elapsed < self.REGISTRATION_INTERVAL_SECONDS:
                    wait_seconds = int(self.REGISTRATION_INTERVAL_SECONDS - elapsed)
                    logger.warning(
                        "ip_registration_too_frequent",
                        ip=ip_address,
                        elapsed=elapsed,
                        wait_seconds=wait_seconds
                    )
                    return False, f"注册过于频繁，请{wait_seconds}秒后再试"
        
        return True, ""
    
    async def record_registration(self, ip_address: str) -> None:
        """记录注册事件"""
        if not ip_address or not self.redis:
            return
        
        # 记录最后注册时间
        last_reg_key = f"{self.IP_LAST_REGISTRATION_PREFIX}{ip_address}"
        self.redis.setex(
            last_reg_key,
            self.REGISTRATION_INTERVAL_SECONDS + 60,  # 多保留1分钟
            str(datetime.now().timestamp())
        )
        
        logger.info("registration_recorded", ip=ip_address)
    
    async def is_ip_blacklisted(self, ip_address: str) -> bool:
        """检查IP是否在黑名单"""
        if not self.redis:
            return False
        
        blacklist_key = f"{self.IP_BLACKLIST_PREFIX}{ip_address}"
        return self.redis.exists(blacklist_key) > 0
    
    async def add_ip_to_blacklist(
        self,
        ip_address: str,
        reason: str,
        duration_hours: int = 24
    ) -> None:
        """
        将IP加入黑名单
        
        Args:
            ip_address: IP地址
            reason: 封禁原因
            duration_hours: 封禁时长（小时），0表示永久
        """
        if not self.redis:
            logger.warning("redis_unavailable_cannot_blacklist_ip", ip=ip_address)
            return
        
        blacklist_key = f"{self.IP_BLACKLIST_PREFIX}{ip_address}"
        
        if duration_hours > 0:
            self.redis.setex(
                blacklist_key,
                duration_hours * 3600,
                reason
            )
        else:
            self.redis.set(blacklist_key, reason)
        
        logger.warning(
            "ip_added_to_blacklist",
            ip=ip_address,
            reason=reason,
            duration_hours=duration_hours
        )
    
    async def remove_ip_from_blacklist(self, ip_address: str) -> None:
        """将IP从黑名单移除"""
        if not self.redis:
            return
        
        blacklist_key = f"{self.IP_BLACKLIST_PREFIX}{ip_address}"
        self.redis.delete(blacklist_key)
        logger.info("ip_removed_from_blacklist", ip=ip_address)
    
    async def check_user_agent_suspicious(self, user_agent: Optional[str]) -> bool:
        """
        检查User-Agent是否可疑
        
        可疑特征：
        - 空User-Agent
        - 包含常见爬虫标识
        - 过短或过长
        """
        if not user_agent:
            return True  # 空UA可疑
        
        if len(user_agent) < 10 or len(user_agent) > 1000:
            return True
        
        # 检查常见爬虫标识
        suspicious_keywords = [
            "bot", "crawler", "spider", "scraper", "curl", "wget",
            "python-requests", "java", "scrapy", "httpclient"
        ]
        
        user_agent_lower = user_agent.lower()
        for keyword in suspicious_keywords:
            if keyword in user_agent_lower:
                return True
        
        return False
    
    async def get_registration_stats_by_ip(
        self,
        ip_address: str,
        days: int = 7
    ) -> dict:
        """
        获取IP的注册统计
        
        Returns:
            {
                "ip": "192.168.1.1",
                "total_registrations": 10,
                "registrations_today": 2,
                "registrations_last_7_days": 8,
                "is_blacklisted": False,
                "recent_users": [...]
            }
        """
        # 使用Repository获取统计数据
        total_count = await self.user_repo.count_registrations_by_ip_total(ip_address)
        today_count = await self.user_repo.count_registrations_by_ip_today(ip_address)
        
        days_ago = datetime.now() - timedelta(days=days)
        days_count = await self.user_repo.count_registrations_by_ip_since(
            ip_address, 
            days_ago
        )
        
        # 获取最近注册的用户
        recent_users_list = await self.user_repo.get_recent_users_by_ip(ip_address, limit=10)
        recent_users = [
            {
                "user_id": user.id,
                "phone": user.phone,
                "created_at": user.created_at.isoformat()
            }
            for user in recent_users_list
        ]
        
        return {
            "ip": ip_address,
            "total_registrations": total_count,
            "registrations_today": today_count,
            f"registrations_last_{days}_days": days_count,
            "is_blacklisted": await self.is_ip_blacklisted(ip_address),
            "recent_users": recent_users
        }


def get_anti_fraud_service(db: AsyncSession) -> AntiFraudService:
    """获取防刷服务实例"""
    return AntiFraudService(db)
