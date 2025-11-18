"""
Template Share Model
模板分享模型
"""
import enum
from typing import List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.user_custom_template import UserCustomTemplate
    from app.models.template_usage_record import TemplateUsageRecord
    from app.models.template_like import TemplateLike


class ShareType(str, enum.Enum):
    """分享类型枚举"""
    PUBLIC = "public"
    FAMILY = "family"
    PRIVATE_LINK = "private_link"


class TemplateShare(Base):
    """模板分享表"""
    __tablename__ = "template_shares"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="分享ID")
    template_id: Mapped[int] = mapped_column(ForeignKey("user_custom_templates.id"), comment="用户模板ID")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), comment="分享者ID")
    share_type: Mapped[ShareType] = mapped_column(Enum(ShareType), index=True, comment="分享类型")
    family_group_id: Mapped[int | None] = mapped_column(ForeignKey("family_groups.id"), nullable=True, comment="家庭组ID（仅家庭分享）")
    share_code: Mapped[str] = mapped_column(String(10), unique=True, index=True, comment="分享码")
    share_title: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="分享标题")
    share_description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="分享描述")
    usage_count: Mapped[int] = mapped_column(default=0, comment="使用次数")
    like_count: Mapped[int] = mapped_column(default=0, comment="点赞数")
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否有效")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), comment="创建时间")
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True, comment="过期时间")
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="template_shares")
    template: Mapped["UserCustomTemplate"] = relationship(back_populates="shares")
    usage_records: Mapped[List["TemplateUsageRecord"]] = relationship(back_populates="template_share", cascade="all, delete-orphan")
    likes: Mapped[List["TemplateLike"]] = relationship(back_populates="template_share", cascade="all, delete-orphan")
