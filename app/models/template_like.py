"""
Template Like Model
模板点赞模型
"""
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.template_share import TemplateShare
    from app.models.user import User


class TemplateLike(Base):
    """模板点赞表"""
    __tablename__ = "template_likes"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="点赞ID")
    template_share_id: Mapped[int] = mapped_column(ForeignKey("template_shares.id"), comment="分享模板ID")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), comment="点赞用户ID")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), comment="点赞时间")
    
    # Relationships
    template_share: Mapped["TemplateShare"] = relationship(back_populates="likes")
    user: Mapped["User"] = relationship(back_populates="template_likes")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('template_share_id', 'user_id', name='uq_template_user_like'),
    )
