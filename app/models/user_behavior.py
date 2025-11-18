"""
User Behavior Model
用户行为分析模型
"""
from typing import List, TYPE_CHECKING
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import Date, Numeric, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserBehavior(Base):
    """用户行为分析表"""
    __tablename__ = "user_behaviors"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="记录ID")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), comment="用户ID")
    behavior_date: Mapped[date] = mapped_column(Date, comment="行为日期")
    active_hours: Mapped[List[int] | None] = mapped_column(type_=JSON, nullable=True, comment="活跃时段(JSON): [8, 9, 18, 19, 20]")
    confirm_avg_response_minutes: Mapped[int | None] = mapped_column(nullable=True, comment="平均响应时间(分钟)")
    completion_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True, comment="完成率")
    most_used_categories: Mapped[List[str] | None] = mapped_column(type_=JSON, nullable=True, comment="常用分类(JSON): ['rent', 'health']")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), comment="创建时间")
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="behaviors")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'behavior_date', name='uq_user_behavior_date'),
    )
