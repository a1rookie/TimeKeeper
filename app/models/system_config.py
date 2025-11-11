"""
SystemConfig Model
系统配置模型
"""

from sqlalchemy import Column, BigInteger, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class SystemConfig(Base):
    """SystemConfig table - 系统配置表"""
    __tablename__ = "system_configs"
    
    id = Column(BigInteger, primary_key=True, index=True, comment="配置ID")
    config_key = Column(String(100), unique=True, nullable=False, comment="配置键")
    config_value = Column(JSON, nullable=False, comment="配置值JSON")
    description = Column(Text, nullable=True, comment="配置描述")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
