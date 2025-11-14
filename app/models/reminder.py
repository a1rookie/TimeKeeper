"""
Reminder Model
提醒数据模型 - 核心表
"""

from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, JSON, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.family_group import FamilyGroup
    from app.models.reminder_template import ReminderTemplate
    from app.models.push_task import PushTask
    from app.models.reminder_completion import ReminderCompletion


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
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="提醒ID")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment="用户ID")
    family_group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("family_groups.id"), nullable=True, index=True, comment="家庭组ID")
    template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reminder_templates.id"), nullable=True, comment="模板ID")
    
    # Basic info
    title: Mapped[str] = mapped_column(String(200), comment="提醒标题")
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True, comment="提醒描述")
    category: Mapped[ReminderCategory] = mapped_column(SQLEnum(ReminderCategory), comment="分类")
    priority: Mapped[int] = mapped_column(default=1, comment="优先级: 1=普通, 2=重要, 3=紧急")
    
    # Recurrence configuration
    recurrence_type: Mapped[RecurrenceType] = mapped_column(SQLEnum(RecurrenceType), comment="周期类型")
    recurrence_config: Mapped[Dict[str, Any]] = mapped_column(type_=JSON, default=dict, comment="周期配置(JSON)")
    
    # Time management
    first_remind_time: Mapped[datetime] = mapped_column(comment="首次提醒时间")
    next_remind_time: Mapped[datetime] = mapped_column(index=True, comment="下次提醒时间")
    last_remind_time: Mapped[Optional[datetime]] = mapped_column(nullable=True, comment="上次提醒时间")
    
    # Reminder settings
    remind_channels: Mapped[List[str]] = mapped_column(type_=JSON, default=list, comment="提醒渠道(JSON): app, sms, wechat, call")
    advance_minutes: Mapped[int] = mapped_column(default=0, comment="提前提醒分钟数")
    
    # Extended fields
    amount: Mapped[Optional[int]] = mapped_column(nullable=True, comment="金额(分)")
    location: Mapped[Optional[Dict[str, Any]]] = mapped_column(type_=JSON, nullable=True, comment="位置信息")
    attachments: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(type_=JSON, nullable=True, comment="附件列表")
    
    # Status
    is_active: Mapped[bool] = mapped_column(default=True, index=True, comment="是否启用")
    is_completed: Mapped[bool] = mapped_column(default=False, comment="是否已完成")
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True, comment="完成时间")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="reminders")
    family_group: Mapped[Optional["FamilyGroup"]] = relationship(back_populates="reminders")
    template: Mapped[Optional["ReminderTemplate"]] = relationship(back_populates="reminders")
    push_tasks: Mapped[List["PushTask"]] = relationship(back_populates="reminder", cascade="all, delete-orphan")
    completions: Mapped[List["ReminderCompletion"]] = relationship(back_populates="reminder", cascade="all, delete-orphan")
