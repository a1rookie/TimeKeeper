"""
Application Configuration
应用配置管理
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # App Info
    APP_NAME: str = "TimeKeeper API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/timekeeper"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # SMS (短信) 配置 - 使用环境变量设置实际密钥
    SMS_PROVIDER: str = "aliyun"  # aliyun or noop
    ALIYUN_ACCESS_KEY_ID: Optional[str] = None
    ALIYUN_ACCESS_KEY_SECRET: Optional[str] = None
    SMS_SIGN_NAME: Optional[str] = None
    SMS_TEMPLATE_CODE: Optional[str] = None
    SMS_REGION: Optional[str] = "cn-hangzhou"
    SMS_CODE_EXPIRE_SECONDS: int = 300  # 验证码过期时间（秒）
    SMS_RATE_LIMIT_SECONDS: int = 60  # 相同手机同用途最小发送间隔
    
    # SMS 防刷限制
    MAX_VERIFY_ATTEMPTS: int = 5  # 单个验证码最多尝试次数
    MAX_SMS_PER_PHONE_PER_DAY: int = 10  # 每个手机号每天最多发送次数
    MAX_SMS_PER_IP_PER_DAY: int = 50  # 每个IP每天最多发送次数
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    
    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
    
    # Push Services - 极光推送
    JPUSH_APP_KEY: Optional[str] = None
    JPUSH_MASTER_SECRET: Optional[str] = None
    JPUSH_ENABLED: bool = False
    
    # Voice Recognition (to be configured later)
    ASR_APP_ID: Optional[str] = None
    ASR_API_KEY: Optional[str] = None
    
    # LLM API (DeepSeek)
    LLM_API_KEY: Optional[str] = None
    LLM_API_URL: str = "https://api.deepseek.com/v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略未定义的额外字段


settings = Settings()
