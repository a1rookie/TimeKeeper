"""
FamilyGroup Model
家庭组模型
"""

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class FamilyGroup(Base):
    """FamilyGroup table - 家庭组表"""
    __tablename__ = "family_groups"
    
    id = Column(BigInteger, primary_key=True, index=True, comment="家庭组ID")
    name = Column(String(100), nullable=False, comment="家庭组名称")
    creator_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, comment="创建者ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # Relationships
    creator = relationship("User", back_populates="created_family_groups", foreign_keys=[creator_id])
    members = relationship("FamilyMember", back_populates="group", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="family_group")
