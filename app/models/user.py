"""
User Model
用户数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    """User table - 用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    phone = Column(String(20), unique=True, index=True, nullable=False, comment="手机号")
    hashed_password = Column(String(255), nullable=False, comment="密码哈希")
    nickname = Column(String(50), nullable=True, comment="昵称")
    avatar_url = Column(String(255), nullable=True, comment="头像URL")
    settings = Column(JSON, default={}, comment="用户设置(JSON)")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # Relationships
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    push_tasks = relationship("PushTask", back_populates="user", cascade="all, delete-orphan")
    reminder_completions = relationship("ReminderCompletion", back_populates="user", cascade="all, delete-orphan")
    
    # Family relationships
    created_family_groups = relationship("FamilyGroup", back_populates="creator", foreign_keys="FamilyGroup.creator_id")
    family_memberships = relationship("FamilyMember", back_populates="user", cascade="all, delete-orphan")
    
    # Template relationships
    custom_templates = relationship("UserCustomTemplate", back_populates="user", cascade="all, delete-orphan")
    template_shares = relationship("TemplateShare", back_populates="owner", cascade="all, delete-orphan")
    template_usage_records = relationship("TemplateUsageRecord", back_populates="user", cascade="all, delete-orphan")
    template_likes = relationship("TemplateLike", back_populates="user", cascade="all, delete-orphan")
    
    # Other relationships
    voice_inputs = relationship("VoiceInput", back_populates="user", cascade="all, delete-orphan")
    push_logs = relationship("PushLog", back_populates="user", cascade="all, delete-orphan")
    behaviors = relationship("UserBehavior", back_populates="user", cascade="all, delete-orphan")
