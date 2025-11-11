"""
UserCustomTemplate Model
用户自定义模板模型
"""

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserCustomTemplate(Base):
    """UserCustomTemplate table - 用户自定义模板表"""
    __tablename__ = "user_custom_templates"
    
    id = Column(BigInteger, primary_key=True, index=True, comment="模板ID")
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    name = Column(String(100), nullable=False, comment="模板名称")
    title_template = Column(String(200), nullable=True, comment="标题模板")
    description_template = Column(Text, nullable=True, comment="描述模板")
    recurrence_type = Column(String(20), nullable=True, comment="周期类型")
    recurrence_config = Column(JSON, nullable=True, comment="周期配置")
    advance_days = Column(Integer, nullable=True, comment="提前天数")
    category = Column(String(50), nullable=True, comment="分类")
    created_from_template_id = Column(BigInteger, ForeignKey("reminder_templates.id"), nullable=True, comment="来源模板ID")
    usage_count = Column(Integer, default=0, comment="使用次数")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # Relationships
    user = relationship("User", back_populates="custom_templates")
    source_template = relationship("ReminderTemplate", foreign_keys=[created_from_template_id])
