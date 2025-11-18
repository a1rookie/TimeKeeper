"""
Reminder Template Model
系统提醒模板模型
"""
from typing import List, Dict, Any, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Text, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSON
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.reminder import Reminder
    from app.models.user_custom_template import UserCustomTemplate


class ReminderTemplate(Base):
    """系统提醒模板表"""
    __tablename__ = "reminder_templates"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="模板ID")
    category: Mapped[str] = mapped_column(String(50), index=True, comment="分类")
    name: Mapped[str] = mapped_column(String(100), comment="模板名称")
    title_template: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="标题模板")
    description_template: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述模板")
    default_recurrence_type: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="默认周期类型")
    default_recurrence_config: Mapped[Dict[str, Any] | None] = mapped_column(type_=JSON, nullable=True, comment="默认周期配置")
    default_advance_days: Mapped[int] = mapped_column(default=3, comment="默认提前天数")
    suggested_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True, comment="建议金额")
    suggested_attachments: Mapped[List[Dict[str, Any]] | None] = mapped_column(type_=JSON, nullable=True, comment="建议附件")
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="图标")
    is_system: Mapped[bool] = mapped_column(default=True, comment="是否系统模板")
    usage_count: Mapped[int] = mapped_column(default=0, comment="使用次数")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), comment="创建时间")
    
    # Relationships
    reminders: Mapped[List["Reminder"]] = relationship(back_populates="template")
    custom_templates: Mapped[List["UserCustomTemplate"]] = relationship(back_populates="base_template")
