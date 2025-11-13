"""
SmsService 抽象与 Aliyun 实现

设计原则：
- 不在代码中硬编码密钥，使用 `app.core.config.settings` 读取环境变量
- 使用 Redis 存储验证码和值（5分钟过期），并实现简单的限频（每个手机号每用途60秒）
- 抽象 SmsService，便于未来替换短信提供商
- 记录所有短信到数据库用于审计和防刷
"""
from __future__ import annotations
from typing import Optional, Tuple
import json
import random
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class SmsService:
    """短信发送服务抽象"""

    def send_sms(self, phone_number: str, sign_name: str, template_code: str, template_param: str) -> bool:
        """发送短信，返回是否成功"""
        raise NotImplementedError()


class NoopSmsService(SmsService):
    """不实际发送，仅记录日志（用于开发或当未配置提供商时）"""

    def send_sms(self, phone_number: str, sign_name: str, template_code: str, template_param: str) -> bool:
        logger.info(f"[NOOP SMS] to={phone_number} sign={sign_name} template={template_code} param={template_param}")
        return True


class AliyunSmsService(SmsService):
    """阿里云短信实现（个人测试模式）：
    使用 alibabacloud_dypnsapi20170525 SDK（号码认证服务）
    """

    def __init__(self):
        self.access_key_id = settings.ALIYUN_ACCESS_KEY_ID
        self.access_key_secret = settings.ALIYUN_ACCESS_KEY_SECRET
        # 延迟导入第三方SDK，避免未安装时启动失败
        try:
            from alibabacloud_dypnsapi20170525.client import Client as Dypnsapi20170525Client
            from alibabacloud_dypnsapi20170525 import models as dypnsapi_20170525_models
            from alibabacloud_tea_openapi import models as open_api_models
            from alibabacloud_tea_util import models as util_models
            
            config = open_api_models.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret,
                endpoint='dypnsapi.aliyuncs.com'
            )
            self.client = Dypnsapi20170525Client(config)
            self.models = dypnsapi_20170525_models
            self.runtime_models = util_models
            self.sdk_available = True
        except Exception as e:
            logger.warning(f"Failed to initialize Aliyun SMS SDK: {e}")
            self.client = None
            self.models = None
            self.runtime_models = None
            self.sdk_available = False

    def send_sms(self, phone_number: str, sign_name: str, template_code: str, template_param: str) -> bool:
        # 参数检查
        if not (self.access_key_id and self.access_key_secret and self.sdk_available):
            logger.warning("Aliyun SMS not configured or SDK not installed - falling back to noop")
            return NoopSmsService().send_sms(phone_number, sign_name, template_code, template_param)

        try:
            # 使用个人测试模式的号码认证服务API
            request = self.models.SendSmsVerifyCodeRequest(
                sign_name=sign_name,
                template_code=template_code,
                phone_number=phone_number,
                template_param=template_param
            )
            
            runtime = self.runtime_models.RuntimeOptions()
            response = self.client.send_sms_verify_code_with_options(request, runtime)
            
            # SendSmsVerifyCodeResponseBody 的属性名称不同
            code = getattr(response.body, 'code', None)
            message = getattr(response.body, 'message', None)
            
            logger.info(f"Aliyun SMS response: Code={code}, Message={message}")
            
            if code == 'OK':
                return True
            else:
                logger.warning(f"Aliyun SMS send failed: {code} - {message}")
                return False
        except Exception as e:
            logger.exception(f"Aliyun SMS exception: {e}")
            return False


# 工厂函数
def get_sms_service() -> SmsService:
    if settings.SMS_PROVIDER == 'aliyun':
        return AliyunSmsService()
    return NoopSmsService()


# Helper: generate code and store in redis + database
def generate_and_store_code(
    phone: str,
    purpose: str = 'register',
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    db: Optional[Session] = None
) -> Tuple[str, Optional[int]]:
    """
    生成6位数字验证码并存入Redis和数据库
    
    Returns:
        (code, log_id) - 验证码和数据库日志ID
        
    Raises:
        RuntimeError: Redis不可用 / 超过限制
    """
    redis_client = get_redis()
    if not redis_client:
        raise RuntimeError('Redis unavailable')

    # 如果提供了数据库连接，执行防刷检查
    if db:
        from app.repositories.sms_log_repository import SmsLogRepository
        sms_repo = SmsLogRepository(db)
        
        # 检查手机号每日发送次数
        phone_count_today = sms_repo.count_by_phone_today(phone, purpose)
        if phone_count_today >= settings.MAX_SMS_PER_PHONE_PER_DAY:
            raise RuntimeError(f'手机号 {phone} 今日发送次数已达上限')
        
        # 检查IP每日发送次数
        if ip_address:
            ip_count_today = sms_repo.count_by_ip_today(ip_address)
            if ip_count_today >= settings.MAX_SMS_PER_IP_PER_DAY:
                raise RuntimeError(f'IP {ip_address} 今日发送次数已达上限')
        
        # 检查1分钟内重复发送
        recent_count = sms_repo.count_recent(phone, purpose, minutes=1)
        if recent_count > 0:
            raise RuntimeError('发送过于频繁，请稍后再试')

    key = f"sms:{purpose}:{phone}"
    rl_key = f"sms:rl:{purpose}:{phone}"

    # Redis限频检查（双重保险）
    if redis_client.exists(rl_key):
        raise RuntimeError('请勿频繁发送验证码')

    # 生成6位验证码
    code = f"{random.randint(0, 999999):06d}"
    
    # 存储到Redis
    redis_client.set(key, code, ex=settings.SMS_CODE_EXPIRE_SECONDS)
    # 设置限频标记
    redis_client.set(rl_key, '1', ex=settings.SMS_RATE_LIMIT_SECONDS)
    
    # 存储到数据库（用于审计）
    log_id = None
    if db:
        expires_at = datetime.now() + timedelta(seconds=settings.SMS_CODE_EXPIRE_SECONDS)
        log = sms_repo.create(
            phone=phone,
            purpose=purpose,
            code=code[:3] + "***",  # 脱敏存储
            ip_address=ip_address,
            user_agent=user_agent,
            provider=settings.SMS_PROVIDER or "noop",
            expires_at=expires_at
        )
        log_id = log.id
    
    return code, log_id


def verify_code(
    phone: str,
    code: str,
    purpose: str = 'register',
    db: Optional[Session] = None
) -> bool:
    """
    验证短信验证码
    
    Returns:
        True if valid, False otherwise
    """
    redis_client = get_redis()
    if not redis_client:
        raise RuntimeError('Redis unavailable')
    
    # 检查验证尝试次数
    if db:
        from app.repositories.sms_log_repository import SmsLogRepository
        sms_repo = SmsLogRepository(db)
        
        # 获取最新未验证记录
        latest_log = sms_repo.get_latest_unverified(phone, purpose)
        if latest_log and latest_log.verify_attempts >= settings.MAX_VERIFY_ATTEMPTS:
            raise RuntimeError('验证码尝试次数过多，请重新获取')
    
    key = f"sms:{purpose}:{phone}"
    value = redis_client.get(key)
    
    # 记录尝试次数
    if db:
        attempts = sms_repo.increment_verify_attempts(phone, purpose)
        logger.info(f"Verify attempt for {phone}/{purpose}: {attempts}/{settings.MAX_VERIFY_ATTEMPTS}")
    
    if not value:
        return False
    
    if value == code:
        # 验证成功，删除Redis中的验证码
        redis_client.delete(key)
        
        # 标记数据库记录为已验证
        if db and latest_log:
            sms_repo.mark_verified(latest_log.id)
        
        return True
    
    return False


def update_sms_log_status(
    db: Session,
    log_id: int,
    status: str,
    error_message: Optional[str] = None
):
    """更新短信日志发送状态"""
    from app.repositories.sms_log_repository import SmsLogRepository
    sms_repo = SmsLogRepository(db)
    sms_repo.update_status(log_id, status, error_message)
