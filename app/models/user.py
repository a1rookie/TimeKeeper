"""
User Model
用户数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    """User table"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    phone = Column(String(20), unique=True, index=True, nullable=False, comment="手机号")
    hashed_password = Column(String(255), nullable=False, comment="密码哈希")
    nickname = Column(String(50), nullable=True, comment="昵称")
    avatar_url = Column(String(255), nullable=True, comment="头像URL")
    settings = Column(JSON, default={}, comment="用户设置(JSON)")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # Relationships
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    push_tasks = relationship("PushTask", back_populates="user", cascade="all, delete-orphan")
