"""
Template Usage Record Model
模板使用记录模型
"""
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Text, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.template_share import TemplateShare
    from app.models.user import User
    from app.models.reminder import Reminder


class TemplateUsageRecord(Base):
    """模板使用记录表"""
    __tablename__ = "template_usage_records"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="记录ID")
    template_share_id: Mapped[int] = mapped_column(ForeignKey("template_shares.id"), index=True, comment="分享模板ID")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment="使用者ID")
    reminder_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reminders.id"), nullable=True, comment="创建的提醒ID")
    used_at: Mapped[datetime] = mapped_column(server_default=func.now(), comment="使用时间")
    feedback_rating: Mapped[Optional[int]] = mapped_column(nullable=True, comment="评分 1-5")
    feedback_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="评价内容")
    
    # Relationships
    template_share: Mapped["TemplateShare"] = relationship(back_populates="usage_records")
    user: Mapped["User"] = relationship(back_populates="template_usage_records")
    reminder: Mapped[Optional["Reminder"]] = relationship()
    
    # Constraints
    __table_args__ = (
        CheckConstraint('feedback_rating >= 1 AND feedback_rating <= 5', name='check_rating_range'),
    )
