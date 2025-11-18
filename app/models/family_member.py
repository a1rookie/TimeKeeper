"""
Family Member Model
家庭成员模型
"""
import enum
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, ForeignKey, Enum, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.family_group import FamilyGroup
    from app.models.user import User


class MemberRole(str, enum.Enum):
    """成员角色枚举"""
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class FamilyMember(Base):
    """家庭成员表"""
    __tablename__ = "family_members"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="成员关系ID")
    group_id: Mapped[int] = mapped_column(ForeignKey("family_groups.id"), comment="家庭组ID")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), comment="用户ID")
    role: Mapped[MemberRole] = mapped_column(Enum(MemberRole), default=MemberRole.MEMBER, comment="角色")
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="在家庭组中的昵称")
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否激活")
    joined_at: Mapped[datetime] = mapped_column(server_default=func.now(), comment="加入时间")
    
    # Relationships
    group: Mapped["FamilyGroup"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="family_memberships")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('group_id', 'user_id', name='uq_group_user'),
    )
