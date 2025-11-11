"""
Template Usage Record Model
模板使用记录模型
"""
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class TemplateUsageRecord(Base):
    """模板使用记录表"""
    __tablename__ = "template_usage_records"
    
    id = Column(Integer, primary_key=True, index=True, comment="记录ID")
    template_share_id = Column(Integer, ForeignKey("template_shares.id"), nullable=False, index=True, comment="分享模板ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="使用者ID")
    reminder_id = Column(Integer, ForeignKey("reminders.id"), comment="创建的提醒ID")
    used_at = Column(DateTime(timezone=True), server_default=func.now(), comment="使用时间")
    feedback_rating = Column(Integer, comment="评分 1-5")
    feedback_comment = Column(Text, comment="评价内容")
    
    # Relationships
    template_share = relationship("TemplateShare", back_populates="usage_records")
    user = relationship("User", back_populates="template_usage_records")
    reminder = relationship("Reminder")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('feedback_rating >= 1 AND feedback_rating <= 5', name='check_rating_range'),
    )
