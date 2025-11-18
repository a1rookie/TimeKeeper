"""
Application Configuration
应用配置管理
"""

from pydantic_settings import BaseSettings


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
    ALIYUN_ACCESS_KEY_ID: str | None = None
    ALIYUN_ACCESS_KEY_SECRET: str | None = None
    SMS_SIGN_NAME: str | None = None
    SMS_TEMPLATE_CODE: str | None = None
    SMS_REGION: str | None = "cn-hangzhou"
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
    JPUSH_APP_KEY: str | None = None
    JPUSH_MASTER_SECRET: str | None = None
    JPUSH_ENABLED: bool = False
    
    # ===== 语音识别服务配置 (ASR) =====
    # 科大讯飞（主力）
    XFYUN_APP_ID: str | None = None
    XFYUN_API_KEY: str | None = None
    XFYUN_API_SECRET: str | None = None
    XFYUN_ENABLED: bool = False
    
    # 百度语音（备用）
    BAIDU_APP_ID: str | None = None
    BAIDU_API_KEY: str | None = None
    BAIDU_SECRET_KEY: str | None = None
    BAIDU_ENABLED: bool = False
    
    # ASR 通用配置
    ASR_TIMEOUT: int = 10  # 语音识别超时时间（秒）
    ASR_MAX_AUDIO_SIZE: int = 5 * 1024 * 1024  # 最大音频文件大小 5MB
    
    # ===== 意图理解服务配置 (NLU) =====
    # DeepSeek-V3 大模型
    DEEPSEEK_API_KEY: str | None = None
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1/chat/completions"
    DEEPSEEK_MODEL: str = "deepseek-chat"  # 或 deepseek-coder
    DEEPSEEK_ENABLED: bool = False
    DEEPSEEK_TIMEOUT: int = 30  # API 调用超时时间（秒）
    DEEPSEEK_MAX_TOKENS: int = 500  # 最大生成 token 数
    
    # NLU 通用配置
    NLU_CONFIDENCE_THRESHOLD: float = 0.7  # 意图识别置信度阈值
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略未定义的额外字段


settings = Settings()
