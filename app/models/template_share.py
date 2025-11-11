"""
TemplateShare Model
模板分享模型
"""

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class TemplateShare(Base):
    """TemplateShare table - 模板分享表"""
    __tablename__ = "template_shares"
    
    id = Column(BigInteger, primary_key=True, index=True, comment="分享ID")
    template_id = Column(BigInteger, nullable=False, comment="模板ID(关联user_custom_templates或reminder_templates)")
    template_type = Column(String(20), nullable=False, comment="模板类型: user_custom, system")
    owner_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, comment="所有者ID")
    share_type = Column(String(20), nullable=False, index=True, comment="分享类型: public, family, private_link")
    share_code = Column(String(10), unique=True, nullable=False, index=True, comment="分享码")
    share_title = Column(String(200), nullable=True, comment="分享标题")
    share_description = Column(Text, nullable=True, comment="分享描述")
    usage_count = Column(Integer, default=0, comment="使用次数")
    like_count = Column(Integer, default=0, comment="点赞数")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="过期时间")
    
    # Relationships
    owner = relationship("User", back_populates="template_shares")
    usage_records = relationship("TemplateUsageRecord", back_populates="template_share", cascade="all, delete-orphan")
    likes = relationship("TemplateLike", back_populates="template_share", cascade="all, delete-orphan")
