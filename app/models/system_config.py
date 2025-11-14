"""
System Config Model
系统配置模型
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import String, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_configs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="配置ID")
    config_key: Mapped[str] = mapped_column(String(100), unique=True, comment="配置键")
    config_value: Mapped[Dict[str, Any]] = mapped_column(type_=JSON, comment="配置值(JSON)")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="配置描述")
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), comment="更新时间")
