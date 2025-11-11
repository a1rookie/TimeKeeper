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
