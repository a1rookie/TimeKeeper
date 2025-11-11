"""
FamilyMember Model
家庭成员模型
"""

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class FamilyMember(Base):
    """FamilyMember table - 家庭成员表"""
    __tablename__ = "family_members"
    
    id = Column(BigInteger, primary_key=True, index=True, comment="成员记录ID")
    group_id = Column(BigInteger, ForeignKey("family_groups.id"), nullable=False, comment="家庭组ID")
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, comment="用户ID")
    role = Column(String(20), default="member", comment="角色: admin, member, viewer")
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), comment="加入时间")
    
    # Relationships
    group = relationship("FamilyGroup", back_populates="members")
    user = relationship("User", back_populates="family_memberships")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('group_id', 'user_id', name='uq_group_user'),
    )
