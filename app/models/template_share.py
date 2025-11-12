"""
Template Share Model
模板分享模型
"""
import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ShareType(str, enum.Enum):
    """分享类型枚举"""
    PUBLIC = "public"
    FAMILY = "family"
    PRIVATE_LINK = "private_link"


class TemplateShare(Base):
    """模板分享表"""
    __tablename__ = "template_shares"
    
    id = Column(Integer, primary_key=True, index=True, comment="分享ID")
    template_id = Column(Integer, ForeignKey("user_custom_templates.id"), comment="用户模板ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="分享者ID")
    share_type = Column(Enum(ShareType), nullable=False, index=True, comment="分享类型")
    family_group_id = Column(Integer, ForeignKey("family_groups.id"), comment="家庭组ID（仅家庭分享）")
    share_code = Column(String(10), unique=True, nullable=False, index=True, comment="分享码")
    share_title = Column(String(200), comment="分享标题")
    share_description = Column(Text, comment="分享描述")
    usage_count = Column(Integer, default=0, comment="使用次数")
    like_count = Column(Integer, default=0, comment="点赞数")
    is_active = Column(Boolean, default=True, comment="是否有效")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    expires_at = Column(DateTime(timezone=True), comment="过期时间")
    
    # Relationships
    user = relationship("User", back_populates="template_shares")
    template = relationship("UserCustomTemplate", back_populates="shares")
    usage_records = relationship("TemplateUsageRecord", back_populates="template_share", cascade="all, delete-orphan")
    likes = relationship("TemplateLike", back_populates="template_share", cascade="all, delete-orphan")
