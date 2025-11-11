"""
User Behavior Model
用户行为分析模型
"""
from sqlalchemy import Column, Integer, Date, DateTime, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserBehavior(Base):
    """用户行为分析表"""
    __tablename__ = "user_behaviors"
    
    id = Column(Integer, primary_key=True, index=True, comment="记录ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    behavior_date = Column(Date, nullable=False, comment="行为日期")
    active_hours = Column(JSON, comment="活跃时段(JSON): [8, 9, 18, 19, 20]")
    confirm_avg_response_minutes = Column(Integer, comment="平均响应时间(分钟)")
    completion_rate = Column(Numeric(5, 2), comment="完成率")
    most_used_categories = Column(JSON, comment="常用分类(JSON): ['rent', 'health']")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # Relationships
    user = relationship("User", back_populates="behaviors")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'behavior_date', name='uq_user_behavior_date'),
    )
