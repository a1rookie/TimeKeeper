"""
Template Share Repository
模板分享数据访问层
"""
from typing import List, Optional
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
            if not self.get_by_share_code(code):
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
    
    async def get_by_id(self, share_id: int) -> Optional[TemplateShare]:
        """根据ID查询分享"""
        result = await self.db.execute(select(TemplateShare).filter(TemplateShare.id == share_id))
        return result.scalar_one_or_none()
    
    async def get_by_share_code(self, share_code: str) -> Optional[TemplateShare]:
        """根据分享码查询分享"""
        return self.db.query(TemplateShare).filter(
            and_(
                TemplateShare.share_code == share_code,
                TemplateShare.is_active == True
            )
        ).first()
    
    async def get_public_shares(self, limit: int = 50, offset: int = 0) -> List[TemplateShare]:
        """获取公开分享列表"""
        return self.db.query(TemplateShare).filter(
            and_(
                TemplateShare.share_type == ShareType.PUBLIC,
                TemplateShare.is_active == True
            )
        ).order_by(desc(TemplateShare.like_count)).limit(limit).offset(offset).all()
    
    async def get_family_shares(self, family_group_id: int) -> List[TemplateShare]:
        """获取家庭组分享列表"""
        return self.db.query(TemplateShare).filter(
            and_(
                TemplateShare.share_type == ShareType.FAMILY,
                TemplateShare.family_group_id == family_group_id,
                TemplateShare.is_active == True
            )
        ).order_by(desc(TemplateShare.created_at)).all()
    
    async def get_user_shares(self, user_id: int) -> List[TemplateShare]:
        """获取用户的所有分享"""
        return self.db.query(TemplateShare).filter(
            and_(
                TemplateShare.user_id == user_id,
                TemplateShare.is_active == True
            )
        ).order_by(desc(TemplateShare.created_at)).all()
    
    async def increment_usage(self, share_id: int) -> bool:
        """增加使用次数"""
        share = self.get_by_id(share_id)
        if not share:
            return False
        
        share.usage_count += 1
        await self.db.commit()
        return True
    
    async def increment_like(self, share_id: int) -> bool:
        """增加点赞数"""
        share = self.get_by_id(share_id)
        if not share:
            return False
        
        share.like_count += 1
        await self.db.commit()
        return True
    
    async def decrement_like(self, share_id: int) -> bool:
        """减少点赞数"""
        share = self.get_by_id(share_id)
        if not share:
            return False
        
        if share.like_count > 0:
            share.like_count -= 1
            await self.db.commit()
        return True
    
    async def deactivate(self, share_id: int) -> bool:
        """停用分享"""
        share = self.get_by_id(share_id)
        if not share:
            return False
        
        share.is_active = False
        await self.db.commit()
        return True
