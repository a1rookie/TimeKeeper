"""
ReminderTemplate Model
系统提醒模板模型
"""

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Text, Boolean, Numeric, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ReminderTemplate(Base):
    """ReminderTemplate table - 系统提醒模板表"""
    __tablename__ = "reminder_templates"
    
    id = Column(BigInteger, primary_key=True, index=True, comment="模板ID")
    category = Column(String(50), nullable=False, index=True, comment="分类")
    name = Column(String(100), nullable=False, comment="模板名称")
    title_template = Column(String(200), nullable=True, comment="标题模板")
    description_template = Column(Text, nullable=True, comment="描述模板")
    default_recurrence_type = Column(String(20), nullable=True, comment="默认周期类型")
    default_recurrence_config = Column(JSON, nullable=True, comment="默认周期配置")
    default_advance_days = Column(Integer, default=3, comment="默认提前天数")
    suggested_amount = Column(Numeric(10, 2), nullable=True, comment="建议金额")
    suggested_attachments = Column(JSON, nullable=True, comment="建议附件")
    icon = Column(String(50), nullable=True, comment="图标")
    is_system = Column(Boolean, default=True, comment="是否系统模板")
    usage_count = Column(Integer, default=0, comment="使用次数")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # Relationships
    reminders = relationship("Reminder", back_populates="template")
