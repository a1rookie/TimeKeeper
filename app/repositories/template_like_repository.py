"""
Template Like Repository
模板点赞数据访问层
"""
from typing import List, Optional
from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import and_
from app.models.template_like import TemplateLike


class TemplateLikeRepository:
    """模板点赞数据访问"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def add_like(self, template_share_id: int, user_id: int) -> TemplateLike:
        """添加点赞"""
        # 检查是否已经点赞
        existing = await self.get_like(template_share_id, user_id)
        if existing:
            return existing
        
        like = TemplateLike(
            template_share_id=template_share_id,
            user_id=user_id
        )
        self.db.add(like)
        await self.db.commit()
        await self.db.refresh(like)
        return like
    
    async def remove_like(self, template_share_id: int, user_id: int) -> bool:
        """取消点赞"""
        like = await self.get_like(template_share_id, user_id)
        if not like:
            return False
        
        await self.db.delete(like)
        await self.db.commit()
        return True
    
    async def get_like(self, template_share_id: int, user_id: int) -> TemplateLike | None:
        """查询用户是否点赞了某个模板"""
        stmt = select(TemplateLike).where(
            and_(
                TemplateLike.template_share_id == template_share_id,
                TemplateLike.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def is_liked(self, template_share_id: int, user_id: int) -> bool:
        """检查用户是否点赞"""
        like = await self.get_like(template_share_id, user_id)
        return like is not None
    
    async def get_user_likes(self, user_id: int) -> Sequence[TemplateLike]:
        """获取用户的所有点赞记录"""
        stmt = select(TemplateLike).where(
            TemplateLike.user_id == user_id
        ).order_by(TemplateLike.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_template_likes(self, template_share_id: int) -> Sequence[TemplateLike]:
        """获取模板的所有点赞记录"""
        stmt = select(TemplateLike).where(
            TemplateLike.template_share_id == template_share_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_like_count(self, template_share_id: int) -> int:
        """获取模板的点赞数量"""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(TemplateLike).where(
            TemplateLike.template_share_id == template_share_id
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
