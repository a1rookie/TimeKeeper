"""
User Custom Template Model
用户自定义模板模型
"""
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.reminder_template import ReminderTemplate
    from app.models.template_share import TemplateShare


class UserCustomTemplate(Base):
    """用户自定义模板表"""
    __tablename__ = "user_custom_templates"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="模板ID")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), comment="用户ID")
    name: Mapped[str] = mapped_column(String(100), comment="模板名称")
    title_template: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="标题模板")
    description_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="描述模板")
    recurrence_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="周期类型")
    recurrence_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(type_=JSON, nullable=True, comment="周期配置")
    advance_days: Mapped[Optional[int]] = mapped_column(nullable=True, comment="提前天数")
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="分类")
    created_from_template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reminder_templates.id"), nullable=True, comment="基于的系统模板ID")
    usage_count: Mapped[int] = mapped_column(default=0, comment="使用次数")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), comment="创建时间")
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="custom_templates")
    base_template: Mapped[Optional["ReminderTemplate"]] = relationship(back_populates="custom_templates")
    shares: Mapped[List["TemplateShare"]] = relationship(back_populates="template", cascade="all, delete-orphan")
