"""
UserBehavior Model
用户行为分析模型
"""

from sqlalchemy import Column, Integer, BigInteger, Date, DateTime, Numeric, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserBehavior(Base):
    """UserBehavior table - 用户行为分析表"""
    __tablename__ = "user_behaviors"
    
    id = Column(BigInteger, primary_key=True, index=True, comment="记录ID")
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, comment="用户ID")
    behavior_date = Column(Date, nullable=False, comment="行为日期")
    active_hours = Column(JSON, nullable=True, comment="活跃时段JSON数组")
    confirm_avg_response_minutes = Column(Integer, nullable=True, comment="平均响应时间(分钟)")
    completion_rate = Column(Numeric(5, 2), nullable=True, comment="完成率")
    most_used_categories = Column(JSON, nullable=True, comment="最常用分类JSON数组")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # Relationships
    user = relationship("User", back_populates="behaviors")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'behavior_date', name='uq_user_behavior_date'),
    )
