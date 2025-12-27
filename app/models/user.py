"""
User Model
用户数据模型
"""

from typing import List, Dict, Any, TYPE_CHECKING
from datetime import datetime
import enum
from sqlalchemy import String, JSON, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.reminder import Reminder
    from app.models.push_task import PushTask
    from app.models.reminder_completion import ReminderCompletion
    from app.models.family_group import FamilyGroup
    from app.models.family_member import FamilyMember
    from app.models.user_custom_template import UserCustomTemplate
    from app.models.template_share import TemplateShare
    from app.models.template_usage_record import TemplateUsageRecord
    from app.models.template_like import TemplateLike
    from app.models.voice_input import VoiceInput
    from app.models.push_log import PushLog
    from app.models.user_behavior import UserBehavior


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    USER = "user"              # 普通用户
    ADMIN = "admin"            # 管理员
    SUPER_ADMIN = "super_admin"  # 超级管理员


class User(Base):
    """User table - 用户表"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="用户ID")
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, comment="手机号")
    hashed_password: Mapped[str] = mapped_column(String(255), comment="密码哈希")
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="昵称")
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="头像URL")
    settings: Mapped[Dict[str, Any]] = mapped_column(type_=JSON, default=dict, comment="用户设置(JSON)")
    
    # 账号状态
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否激活")
    is_verified: Mapped[bool] = mapped_column(default=True, comment="是否已验证手机号")
    is_banned: Mapped[bool] = mapped_column(default=False, index=True, comment="是否被封禁")
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.USER, index=True, comment="用户角色")
    ban_reason: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="封禁原因")
    banned_at: Mapped[datetime | None] = mapped_column(nullable=True, comment="封禁时间")
    
    # 注册审计信息
    registration_ip: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True, comment="注册IP地址")
    registration_user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="注册User-Agent")
    registration_source: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="注册来源(web/ios/android)")
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), comment="更新时间")
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True, comment="最后登录时间")
    last_login_ip: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="最后登录IP")
    
    # Relationships
    reminders: Mapped[List["Reminder"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    push_tasks: Mapped[List["PushTask"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reminder_completions: Mapped[List["ReminderCompletion"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    
    # Family relationships
    created_family_groups: Mapped[List["FamilyGroup"]] = relationship(back_populates="creator", foreign_keys="FamilyGroup.creator_id")
    family_memberships: Mapped[List["FamilyMember"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    
    # Template relationships
    custom_templates: Mapped[List["UserCustomTemplate"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    template_shares: Mapped[List["TemplateShare"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    template_usage_records: Mapped[List["TemplateUsageRecord"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    template_likes: Mapped[List["TemplateLike"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    
    # Other relationships
    voice_inputs: Mapped[List["VoiceInput"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    push_logs: Mapped[List["PushLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    behaviors: Mapped[List["UserBehavior"]] = relationship(back_populates="user", cascade="all, delete-orphan")
