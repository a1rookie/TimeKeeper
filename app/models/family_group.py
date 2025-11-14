"""
Family Group Model
家庭组模型
"""
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.family_member import FamilyMember
    from app.models.reminder import Reminder


class FamilyGroup(Base):
    """家庭组表"""
    __tablename__ = "family_groups"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="家庭组ID")
    name: Mapped[str] = mapped_column(String(100), comment="家庭组名称")
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), comment="创建者ID")
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否有效")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), comment="创建时间")
    
    # Relationships
    creator: Mapped["User"] = relationship(back_populates="created_family_groups", foreign_keys=[creator_id])
    members: Mapped[List["FamilyMember"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    reminders: Mapped[List["Reminder"]] = relationship(back_populates="family_group")
