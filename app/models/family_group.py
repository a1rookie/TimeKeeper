"""
Family Group Model
家庭组模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class FamilyGroup(Base):
    """家庭组表"""
    __tablename__ = "family_groups"
    
    id = Column(Integer, primary_key=True, index=True, comment="家庭组ID")
    name = Column(String(100), nullable=False, comment="家庭组名称")
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建者ID")
    is_active = Column(Boolean, default=True, comment="是否有效")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # Relationships
    creator = relationship("User", back_populates="created_family_groups", foreign_keys=[creator_id])
    members = relationship("FamilyMember", back_populates="group", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="family_group")
