"""
User Custom Template Model
用户自定义模板模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserCustomTemplate(Base):
    """用户自定义模板表"""
    __tablename__ = "user_custom_templates"
    
    id = Column(Integer, primary_key=True, index=True, comment="模板ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    name = Column(String(100), nullable=False, comment="模板名称")
    title_template = Column(String(200), comment="标题模板")
    description_template = Column(Text, comment="描述模板")
    recurrence_type = Column(String(20), comment="周期类型")
    recurrence_config = Column(JSON, comment="周期配置")
    advance_days = Column(Integer, comment="提前天数")
    category = Column(String(50), comment="分类")
    created_from_template_id = Column(Integer, ForeignKey("reminder_templates.id"), comment="基于的系统模板ID")
    usage_count = Column(Integer, default=0, comment="使用次数")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # Relationships
    user = relationship("User", back_populates="custom_templates")
    base_template = relationship("ReminderTemplate", back_populates="custom_templates")
