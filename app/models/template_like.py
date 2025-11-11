"""
Template Like Model
模板点赞模型
"""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class TemplateLike(Base):
    """模板点赞表"""
    __tablename__ = "template_likes"
    
    id = Column(Integer, primary_key=True, index=True, comment="点赞ID")
    template_share_id = Column(Integer, ForeignKey("template_shares.id"), nullable=False, comment="分享模板ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="点赞用户ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="点赞时间")
    
    # Relationships
    template_share = relationship("TemplateShare", back_populates="likes")
    user = relationship("User", back_populates="template_likes")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('template_share_id', 'user_id', name='uq_template_user_like'),
    )
