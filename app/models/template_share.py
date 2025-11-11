"""
Template Share Model
模板分享模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class TemplateShare(Base):
    """模板分享表"""
    __tablename__ = "template_shares"
    
    id = Column(Integer, primary_key=True, index=True, comment="分享ID")
    template_id = Column(Integer, comment="模板ID (可关联系统或用户模板)")
    template_type = Column(String(20), nullable=False, comment="模板类型: system, user_custom")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="分享者ID")
    share_type = Column(String(20), nullable=False, index=True, comment="分享类型: public, family, private_link")
    share_code = Column(String(10), unique=True, nullable=False, index=True, comment="分享码")
    share_title = Column(String(200), comment="分享标题")
    share_description = Column(Text, comment="分享描述")
    usage_count = Column(Integer, default=0, comment="使用次数")
    like_count = Column(Integer, default=0, comment="点赞数")
    is_active = Column(Boolean, default=True, comment="是否有效")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    expires_at = Column(DateTime(timezone=True), comment="过期时间")
    
    # Relationships
    owner = relationship("User", back_populates="template_shares")
    usage_records = relationship("TemplateUsageRecord", back_populates="template_share", cascade="all, delete-orphan")
    likes = relationship("TemplateLike", back_populates="template_share", cascade="all, delete-orphan")
