"""
Family Member Model
家庭成员模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class FamilyMember(Base):
    """家庭成员表"""
    __tablename__ = "family_members"
    
    id = Column(Integer, primary_key=True, index=True, comment="成员关系ID")
    group_id = Column(Integer, ForeignKey("family_groups.id"), nullable=False, comment="家庭组ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    role = Column(String(20), default="member", comment="角色: admin, member, viewer")
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), comment="加入时间")
    
    # Relationships
    group = relationship("FamilyGroup", back_populates="members")
    user = relationship("User", back_populates="family_memberships")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('group_id', 'user_id', name='uq_group_user'),
    )
