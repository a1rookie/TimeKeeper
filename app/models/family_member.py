"""
Family Member Model
家庭成员模型
"""
import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class MemberRole(str, enum.Enum):
    """成员角色枚举"""
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class FamilyMember(Base):
    """家庭成员表"""
    __tablename__ = "family_members"
    
    id = Column(Integer, primary_key=True, index=True, comment="成员关系ID")
    group_id = Column(Integer, ForeignKey("family_groups.id"), nullable=False, comment="家庭组ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    role = Column(Enum(MemberRole), default=MemberRole.MEMBER, comment="角色")
    nickname = Column(String(50), comment="在家庭组中的昵称")
    is_active = Column(Boolean, default=True, comment="是否激活")
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), comment="加入时间")
    
    # Relationships
    group = relationship("FamilyGroup", back_populates="members")
    user = relationship("User", back_populates="family_memberships")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('group_id', 'user_id', name='uq_group_user'),
    )
