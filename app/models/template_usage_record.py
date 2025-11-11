"""
TemplateUsageRecord Model
模板使用记录模型
"""

from sqlalchemy import Column, Integer, BigInteger, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class TemplateUsageRecord(Base):
    """TemplateUsageRecord table - 模板使用记录表"""
    __tablename__ = "template_usage_records"
    
    id = Column(BigInteger, primary_key=True, index=True, comment="记录ID")
    template_share_id = Column(BigInteger, ForeignKey("template_shares.id"), nullable=False, index=True, comment="分享ID")
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True, comment="使用者ID")
    reminder_id = Column(BigInteger, ForeignKey("reminders.id"), nullable=True, comment="创建的提醒ID")
    used_at = Column(DateTime(timezone=True), server_default=func.now(), comment="使用时间")
    feedback_rating = Column(Integer, nullable=True, comment="评分1-5")
    feedback_comment = Column(Text, nullable=True, comment="评价内容")
    
    # Relationships
    template_share = relationship("TemplateShare", back_populates="usage_records")
    user = relationship("User", back_populates="template_usage_records")
    reminder = relationship("Reminder", back_populates="template_usage_record")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('feedback_rating >= 1 AND feedback_rating <= 5', name='check_rating_range'),
    )
