"""
Template Share Repository
模板分享数据访问层
"""
from typing import Optional
from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import and_, desc
from app.models.template_share import TemplateShare, ShareType
import secrets
import string


class TemplateShareRepository:
    """模板分享数据访问"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _generate_share_code(self) -> str:
        """生成唯一分享码"""
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10))
            if not await self.get_by_share_code(code):
                return code
    
    async def create(
        self,
        template_id: int,
        user_id: int,
        share_type: ShareType,
        share_title: str,
        share_description: Optional[str] = None,
        family_group_id: Optional[int] = None
    ) -> TemplateShare:
        """创建模板分享"""
        share = TemplateShare(
            template_id=template_id,
            user_id=user_id,
            share_type=share_type,
            share_code=self._generate_share_code(),
            share_title=share_title,
            share_description=share_description,
            family_group_id=family_group_id,
            is_active=True,
            usage_count=0,
            like_count=0
        )
        self.db.add(share)
        await self.db.commit()
        await self.db.refresh(share)
        return share
    
    async def get_by_id(self, share_id: int) -> TemplateShare | None:
        """根据ID查询分享"""
        result = await self.db.execute(select(TemplateShare).where(TemplateShare.id == share_id))
        return result.scalar_one_or_none()
    
    async def get_by_share_code(self, share_code: str) -> TemplateShare | None:
        """根据分享码查询分享"""
        stmt = select(TemplateShare).where(
            and_(
                TemplateShare.share_code == share_code,
                TemplateShare.is_active == True
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()
    
    async def get_public_shares(self, limit: int = 50, offset: int = 0) -> Sequence[TemplateShare]:
        """获取公开分享列表"""
        stmt = select(TemplateShare).where(
            and_(
                TemplateShare.share_type == ShareType.PUBLIC,
                TemplateShare.is_active == True
            )
        ).order_by(desc(TemplateShare.like_count)).limit(limit).offset(offset)
        res = await self.db.execute(stmt)
        return res.scalars().all()
    
    async def get_family_shares(self, family_group_id: int) -> Sequence[TemplateShare]:
        """获取家庭组分享列表"""
        stmt = select(TemplateShare).where(
            and_(
                TemplateShare.share_type == ShareType.FAMILY,
                TemplateShare.family_group_id == family_group_id,
                TemplateShare.is_active == True
            )
        ).order_by(desc(TemplateShare.created_at))
        res = await self.db.execute(stmt)
        return res.scalars().all()
    
    async def get_user_shares(self, user_id: int) -> Sequence[TemplateShare]:
        """获取用户的所有分享"""
        stmt = select(TemplateShare).where(
            and_(
                TemplateShare.user_id == user_id,
                TemplateShare.is_active == True
            )
        ).order_by(desc(TemplateShare.created_at))
        res = await self.db.execute(stmt)
        return res.scalars().all()
    
    async def increment_usage(self, share_id: int) -> bool:
        """增加使用次数"""
        share = await self.get_by_id(share_id)
        if not share:
            return False

        share.usage_count = (share.usage_count or 0) + 1
        await self.db.commit()
        return True
    
    async def increment_like(self, share_id: int) -> bool:
        """增加点赞数"""
        share = await self.get_by_id(share_id)
        if not share:
            return False

        share.like_count = (share.like_count or 0) + 1
        await self.db.commit()
        return True
    
    async def decrement_like(self, share_id: int) -> bool:
        """减少点赞数"""
        share = await self.get_by_id(share_id)
        if not share:
            return False

        if share.like_count and share.like_count > 0:
            share.like_count -= 1
            await self.db.commit()
        return True
    
    async def deactivate(self, share_id: int) -> bool:
        """停用分享"""
        share = await self.get_by_id(share_id)
        if not share:
            return False

        share.is_active = False
        await self.db.commit()
        return True
    
    async def can_user_access_template(self, custom_template_id: int, user_id: int) -> bool:
        """
        检查用户是否可以访问指定的自定义模板
        
        访问条件：
        1. 用户是模板创建者
        2. 模板被公开分享
        3. 模板被分享到用户所在的家庭组
        
        Args:
            custom_template_id: 自定义模板ID
            user_id: 用户ID
            
        Returns:
            bool: 是否有访问权限
        """
        from app.models.user_custom_template import UserCustomTemplate
        from app.repositories.family_member_repository import FamilyMemberRepository
        
        # 1. 检查是否为模板创建者
        result = await self.db.execute(
            select(UserCustomTemplate).filter(
                and_(
                    UserCustomTemplate.id == custom_template_id,
                    UserCustomTemplate.user_id == user_id
                )
            )
        )
        if result.scalar_one_or_none():
            return True
        
        # 2. 检查是否有公开分享
        result = await self.db.execute(
            select(TemplateShare).filter(
                and_(
                    TemplateShare.template_id == custom_template_id,
                    TemplateShare.share_type == ShareType.PUBLIC,
                    TemplateShare.is_active == True
                )
            )
        )
        if result.scalar_one_or_none():
            return True
        
        # 3. 检查是否为家庭组分享
        # 获取用户的所有家庭组
        family_repo = FamilyMemberRepository(self.db)
        user_families = await family_repo.get_user_families(user_id)
        
        if user_families:
            family_ids = [f.family_group_id for f in user_families]
            result = await self.db.execute(
                select(TemplateShare).filter(
                    and_(
                        TemplateShare.template_id == custom_template_id,
                        TemplateShare.share_type == ShareType.FAMILY,
                        TemplateShare.family_group_id.in_(family_ids),
                        TemplateShare.is_active == True
                    )
                )
            )
            if result.scalar_one_or_none():
                return True
        
        return False
