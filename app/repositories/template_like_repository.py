"""
Template Like Repository
模板点赞数据访问层
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import and_
from app.models.template_like import TemplateLike


class TemplateLikeRepository:
    """模板点赞数据访问"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def add_like(self, template_share_id: int, user_id: int) -> Optional[TemplateLike]:
        """添加点赞"""
        # 检查是否已经点赞
        existing = self.get_like(template_share_id, user_id)
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
        like = self.get_like(template_share_id, user_id)
        if not like:
            return False
        
        await self.db.delete(like)
        await self.db.commit()
        return True
    
    async def get_like(self, template_share_id: int, user_id: int) -> Optional[TemplateLike]:
        """查询用户是否点赞了某个模板"""
        return self.db.query(TemplateLike).filter(
            and_(
                TemplateLike.template_share_id == template_share_id,
                TemplateLike.user_id == user_id
            )
        ).first()
    
    async def is_liked(self, template_share_id: int, user_id: int) -> bool:
        """检查用户是否点赞"""
        return self.get_like(template_share_id, user_id) is not None
    
    async def get_user_likes(self, user_id: int) -> List[TemplateLike]:
        """获取用户的所有点赞记录"""
        return self.db.query(TemplateLike).filter(
            TemplateLike.user_id == user_id
        ).order_by(TemplateLike.created_at.desc()).all()
    
    async def get_template_likes(self, template_share_id: int) -> List[TemplateLike]:
        """获取模板的所有点赞记录"""
        result = await self.db.execute(select(TemplateLike).filter(
            TemplateLike.template_share_id == template_share_id
        ))
        return list(result.scalars().all())
    
    async def get_like_count(self, template_share_id: int) -> int:
        """获取模板的点赞数量"""
        return self.db.query(TemplateLike).filter(
            TemplateLike.template_share_id == template_share_id
        ).count()
