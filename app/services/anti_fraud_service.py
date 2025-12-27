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
    """注册防刷和登录保护服务"""
    
    # 注册限制配置（可通过环境变量配置）
    MAX_REGISTRATIONS_PER_IP_PER_DAY = 5  # 每个IP每天最多注册5个
    REGISTRATION_INTERVAL_SECONDS = 300  # 同一IP两次注册间隔至少5分钟
    IP_BLACKLIST_PREFIX = "ip_blacklist:"
    IP_REGISTRATION_COUNTER_PREFIX = "ip_reg_count:"
    IP_LAST_REGISTRATION_PREFIX = "ip_last_reg:"
    
    # 登录保护配置
    LOGIN_FAIL_PREFIX = "login_fail:"  # 登录失败计数前缀
    LOGIN_LOCK_PREFIX = "login_lock:"  # 账号锁定前缀
    MAX_LOGIN_ATTEMPTS_BEFORE_SMS = 3  # 3次失败后要求短信验证
    MAX_LOGIN_ATTEMPTS_BEFORE_LOCK = 5  # 5次失败后锁定15分钟
    MAX_LOGIN_ATTEMPTS_BEFORE_LONG_LOCK = 10  # 10次失败后锁定1小时
    SHORT_LOCK_DURATION = 900  # 15分钟（秒）
    LONG_LOCK_DURATION = 3600  # 1小时（秒）
    LOGIN_FAIL_WINDOW = 1800  # 登录失败计数窗口：30分钟
    
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
    
    # ==================== 登录保护功能 ====================
    
    async def check_login_attempts(
        self,
        identifier: str,
        ip_address: str | None = None
    ) -> tuple[bool, str, bool]:
        """
        检查登录尝试次数
        
        Args:
            identifier: 账号标识（手机号）
            ip_address: IP地址（可选）
            
        Returns:
            (is_allowed, error_message, requires_sms)
            - is_allowed: 是否允许登录
            - error_message: 错误信息
            - requires_sms: 是否要求短信验证码
        """
        if not self.redis:
            logger.warning(
                "login_protection_disabled_redis_unavailable",
                identifier=identifier,
                ip=ip_address
            )
            return True, "", False
        
        # 检查账号是否被锁定
        lock_key = f"{self.LOGIN_LOCK_PREFIX}{identifier}"
        if self.redis.exists(lock_key):
            ttl = self.redis.ttl(lock_key)
            minutes = (ttl + 59) // 60  # 向上取整
            logger.warning(
                "login_attempt_on_locked_account",
                identifier=identifier,
                ip=ip_address,
                ttl_seconds=ttl
            )
            return False, f"账号已被临时锁定，请{minutes}分钟后再试", False
        
        # 获取失败次数
        fail_key = f"{self.LOGIN_FAIL_PREFIX}{identifier}"
        fail_count = int(self.redis.get(fail_key) or 0)
        
        # 判断是否需要短信验证码
        requires_sms = fail_count >= self.MAX_LOGIN_ATTEMPTS_BEFORE_SMS
        
        logger.info(
            "login_attempts_check",
            identifier=identifier,
            ip=ip_address,
            fail_count=fail_count,
            requires_sms=requires_sms
        )
        
        return True, "", requires_sms
    
    async def record_login_failure(
        self,
        identifier: str,
        ip_address: str | None = None,
        reason: str = "invalid_credentials"
    ) -> dict:
        """
        记录登录失败
        
        Returns:
            {
                "fail_count": 3,
                "is_locked": False,
                "lock_duration_minutes": 0,
                "requires_sms": True
            }
        """
        if not self.redis:
            logger.warning(
                "login_failure_tracking_disabled_redis_unavailable",
                identifier=identifier,
                ip=ip_address
            )
            return {
                "fail_count": 0,
                "is_locked": False,
                "lock_duration_minutes": 0,
                "requires_sms": False
            }
        
        fail_key = f"{self.LOGIN_FAIL_PREFIX}{identifier}"
        
        # 增加失败计数
        fail_count = self.redis.incr(fail_key)
        
        # 设置过期时间（如果是第一次失败）
        if fail_count == 1:
            self.redis.expire(fail_key, self.LOGIN_FAIL_WINDOW)
        
        is_locked = False
        lock_duration_minutes = 0
        
        # 检查是否需要锁定
        if fail_count >= self.MAX_LOGIN_ATTEMPTS_BEFORE_LONG_LOCK:
            # 10次失败：锁定1小时
            lock_duration = self.LONG_LOCK_DURATION
            lock_duration_minutes = 60
            is_locked = True
        elif fail_count >= self.MAX_LOGIN_ATTEMPTS_BEFORE_LOCK:
            # 5次失败：锁定15分钟
            lock_duration = self.SHORT_LOCK_DURATION
            lock_duration_minutes = 15
            is_locked = True
        
        if is_locked:
            lock_key = f"{self.LOGIN_LOCK_PREFIX}{identifier}"
            self.redis.setex(lock_key, lock_duration, str(fail_count))
            logger.warning(
                "account_temporarily_locked",
                identifier=identifier,
                ip=ip_address,
                fail_count=fail_count,
                lock_duration_minutes=lock_duration_minutes,
                reason=reason
            )
        
        requires_sms = fail_count >= self.MAX_LOGIN_ATTEMPTS_BEFORE_SMS
        
        logger.warning(
            "login_failure_recorded",
            identifier=identifier,
            ip=ip_address,
            fail_count=fail_count,
            requires_sms=requires_sms,
            reason=reason
        )
        
        return {
            "fail_count": fail_count,
            "is_locked": is_locked,
            "lock_duration_minutes": lock_duration_minutes,
            "requires_sms": requires_sms
        }
    
    async def clear_login_failures(self, identifier: str) -> None:
        """清除登录失败记录（登录成功后调用）"""
        if not self.redis:
            return
        
        fail_key = f"{self.LOGIN_FAIL_PREFIX}{identifier}"
        self.redis.delete(fail_key)
        
        logger.info("login_failures_cleared", identifier=identifier)
    
    async def get_login_status(self, identifier: str) -> dict:
        """
        获取账号登录状态
        
        Returns:
            {
                "is_locked": False,
                "fail_count": 2,
                "lock_ttl_seconds": 0,
                "requires_sms": False
            }
        """
        if not self.redis:
            return {
                "is_locked": False,
                "fail_count": 0,
                "lock_ttl_seconds": 0,
                "requires_sms": False
            }
        
        lock_key = f"{self.LOGIN_LOCK_PREFIX}{identifier}"
        fail_key = f"{self.LOGIN_FAIL_PREFIX}{identifier}"
        
        is_locked = self.redis.exists(lock_key) > 0
        lock_ttl = self.redis.ttl(lock_key) if is_locked else 0
        fail_count = int(self.redis.get(fail_key) or 0)
        requires_sms = fail_count >= self.MAX_LOGIN_ATTEMPTS_BEFORE_SMS
        
        return {
            "is_locked": is_locked,
            "fail_count": fail_count,
            "lock_ttl_seconds": lock_ttl,
            "requires_sms": requires_sms
        }


def get_anti_fraud_service(db: AsyncSession) -> AntiFraudService:
    """获取防刷服务实例"""
    return AntiFraudService(db)
