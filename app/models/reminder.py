"""
Reminder Model
提醒数据模型 - 核心表
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class RecurrenceType(str, enum.Enum):
    """周期类型枚举"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class ReminderCategory(str, enum.Enum):
    """提醒分类枚举"""
    RENT = "rent"          # 居住类
    HEALTH = "health"      # 健康类
    PET = "pet"            # 宠物类
    FINANCE = "finance"    # 财务类
    DOCUMENT = "document"  # 证件类
    MEMORIAL = "memorial"  # 纪念类
    OTHER = "other"        # 其他


class Reminder(Base):
    """Reminder table - 核心提醒表"""
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, index=True, comment="提醒ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    family_group_id = Column(Integer, ForeignKey("family_groups.id"), nullable=True, index=True, comment="家庭组ID")
    template_id = Column(Integer, ForeignKey("reminder_templates.id"), nullable=True, comment="模板ID")
    
    # Basic info
    title = Column(String(200), nullable=False, comment="提醒标题")
    description = Column(String(1000), nullable=True, comment="提醒描述")
    category = Column(SQLEnum(ReminderCategory), nullable=False, comment="分类")
    priority = Column(Integer, default=1, comment="优先级: 1=普通, 2=重要, 3=紧急")
    
    # Recurrence configuration
    recurrence_type = Column(SQLEnum(RecurrenceType), nullable=False, comment="周期类型")
    recurrence_config = Column(JSON, default={}, comment="周期配置(JSON)")
    
    # Time management
    first_remind_time = Column(DateTime(timezone=True), nullable=False, comment="首次提醒时间")
    next_remind_time = Column(DateTime(timezone=True), nullable=False, index=True, comment="下次提醒时间")
    last_remind_time = Column(DateTime(timezone=True), nullable=True, comment="上次提醒时间")
    
    # Reminder settings
    remind_channels = Column(JSON, default=["app"], comment="提醒渠道(JSON): app, sms, wechat, call")
    advance_minutes = Column(Integer, default=0, comment="提前提醒分钟数")
    
    # Additional info
    amount = Column(Integer, nullable=True, comment="金额（以分为单位）")
    location = Column(JSON, nullable=True, comment="位置信息(JSON)")
    attachments = Column(JSON, nullable=True, comment="附件列表(JSON)")
    
    # Status
    is_active = Column(Boolean, default=True, index=True, comment="是否启用")
    is_completed = Column(Boolean, default=False, comment="是否已完成")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成时间")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # Relationships
    user = relationship("User", back_populates="reminders")
    family_group = relationship("FamilyGroup", back_populates="reminders")
    template = relationship("ReminderTemplate", back_populates="reminders")
    push_tasks = relationship("PushTask", back_populates="reminder", cascade="all, delete-orphan")
    completions = relationship("ReminderCompletion", back_populates="reminder", cascade="all, delete-orphan")
    push_logs = relationship("PushLog", back_populates="reminder", cascade="all, delete-orphan")
    template_usage_record = relationship("TemplateUsageRecord", back_populates="reminder", uselist=False)
