"""
Family Group Repository
家庭组数据访问层
"""
from collections.abc import Sequence
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import and_
from app.models.family_group import FamilyGroup
from app.models.family_member import FamilyMember


class FamilyGroupRepository:
    """家庭组数据访问"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, name: str, creator_id: int, description: Optional[str] = None) -> FamilyGroup:
        """创建家庭组"""
        group = FamilyGroup(
            name=name,
            creator_id=creator_id,
            description=description,
            is_active=True
        )
        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)
        return group
    
    async def get_by_id(self, group_id: int) -> FamilyGroup | None:
        """根据ID查询家庭组"""
        result = await self.db.execute(select(FamilyGroup).filter(FamilyGroup.id == group_id))
        return result.scalar_one_or_none()
    
    async def get_by_creator(self, creator_id: int) -> Sequence[FamilyGroup]:
        """查询用户创建的所有家庭组"""
        stmt = select(FamilyGroup).where(
            and_(
                FamilyGroup.creator_id == creator_id,
                FamilyGroup.is_active == True
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_user_groups(self, user_id: int) -> Sequence[FamilyGroup]:
        """查询用户所在的所有家庭组（包括创建和加入的）"""
        stmt = select(FamilyGroup).join(
            FamilyMember,
            FamilyGroup.id == FamilyMember.group_id
        ).where(
            and_(
                FamilyMember.user_id == user_id,
                FamilyMember.is_active == True,
                FamilyGroup.is_active == True
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def update(self, group_id: int, **kwargs) -> FamilyGroup | None:
        """更新家庭组信息"""
        group = await self.get_by_id(group_id)
        if not group:
            return None
        
        for key, value in kwargs.items():
            if hasattr(group, key):
                setattr(group, key, value)
        
        await self.db.commit()
        await self.db.refresh(group)
        return group
    
    async def deactivate(self, group_id: int) -> bool:
        """停用家庭组"""
        group = await self.get_by_id(group_id)
        if not group:
            return False
        
        group.is_active = False
        await self.db.commit()
        return True
    
    async def get_member_count(self, group_id: int) -> int:
        """获取家庭组成员数量"""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(FamilyMember).where(
            and_(
                FamilyMember.group_id == group_id,
                FamilyMember.is_active == True
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
