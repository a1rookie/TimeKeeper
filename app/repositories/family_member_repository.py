"""
Family Member Repository
家庭成员数据访问层
"""
from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import and_
from app.models.family_member import FamilyMember, MemberRole


class FamilyMemberRepository:
    """家庭成员数据访问"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def add_member(
        self,
        group_id: int,
        user_id: int,
        role: MemberRole = MemberRole.MEMBER,
        nickname: str | None = None
    ) -> FamilyMember:
        """添加成员到家庭组"""
        member = FamilyMember(
            group_id=group_id,
            user_id=user_id,
            role=role,
            nickname=nickname,
            is_active=True
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member
    
    async def get_by_id(self, member_id: int) -> FamilyMember | None:
        """根据ID查询成员"""
        result = await self.db.execute(select(FamilyMember).filter(FamilyMember.id == member_id))
        return result.scalar_one_or_none()
    
    async def get_member(self, group_id: int, user_id: int) -> FamilyMember | None:
        """查询指定用户在家庭组中的成员信息"""
        stmt = select(FamilyMember).where(
            and_(
                FamilyMember.group_id == group_id,
                FamilyMember.user_id == user_id,
                FamilyMember.is_active == True
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_group_members(self, group_id: int) -> Sequence[FamilyMember]:
        """查询家庭组所有成员"""
        stmt = select(FamilyMember).where(
            and_(
                FamilyMember.group_id == group_id,
                FamilyMember.is_active == True
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def is_member(self, group_id: int, user_id: int) -> bool:
        """检查用户是否为家庭组成员"""
        member = await self.get_member(group_id, user_id)
        return member is not None
    
    async def is_admin(self, group_id: int, user_id: int) -> bool:
        """检查用户是否为管理员"""
        member = await self.get_member(group_id, user_id)
        return member is not None and member.role == MemberRole.ADMIN
    
    async def update_role(self, member_id: int, role: MemberRole) -> FamilyMember | None:
        """更新成员角色"""
        member = await self.get_by_id(member_id)
        if not member:
            return None
        
        member.role = role
        await self.db.commit()
        await self.db.refresh(member)
        return member
    
    async def update_nickname(self, member_id: int, nickname: str) -> FamilyMember | None:
        """更新成员昵称"""
        member = await self.get_by_id(member_id)
        if not member:
            return None
        
        member.nickname = nickname
        await self.db.commit()
        await self.db.refresh(member)
        return member
    
    async def remove_member(self, group_id: int, user_id: int) -> bool:
        """移除成员"""
        member = await self.get_member(group_id, user_id)
        if not member:
            return False
        
        member.is_active = False
        await self.db.commit()
        return True
    
    async def get_user_families(self, user_id: int) -> Sequence[FamilyMember]:
        """获取用户所在的所有家庭组成员记录"""
        stmt = select(FamilyMember).where(
            and_(
                FamilyMember.user_id == user_id,
                FamilyMember.is_active == True
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_user_groups_count(self, user_id: int) -> int:
        """获取用户加入的家庭组数量"""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(FamilyMember).where(
            and_(
                FamilyMember.user_id == user_id,
                FamilyMember.is_active == True
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
