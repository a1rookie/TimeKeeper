"""
User Custom Template Repository
用户自定义模板数据访问层
"""
from collections.abc import Sequence
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import and_
from app.models.user_custom_template import UserCustomTemplate


class UserCustomTemplateRepository:
    """用户自定义模板数据访问"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        recurrence_type: Optional[str] = None,
        recurrence_config: Optional[dict] = None,
        remind_advance_days: int = 0,
        created_from_template_id: Optional[int] = None
    ) -> UserCustomTemplate:
        """创建用户自定义模板"""
        template = UserCustomTemplate(
            user_id=user_id,
            name=name,
            description=description,
            recurrence_type=recurrence_type,
            recurrence_config=recurrence_config,
            remind_advance_days=remind_advance_days,
            created_from_template_id=created_from_template_id
        )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    async def get_by_id(self, template_id: int) -> UserCustomTemplate | None:
        """根据ID查询模板"""
        result = await self.db.execute(select(UserCustomTemplate).where(UserCustomTemplate.id == template_id))
        return result.scalar_one_or_none()
    
    async def get_user_templates(self, user_id: int) -> Sequence[UserCustomTemplate]:
        """查询用户的所有自定义模板"""
        stmt = select(UserCustomTemplate).where(UserCustomTemplate.user_id == user_id).order_by(UserCustomTemplate.created_at.desc())
        res = await self.db.execute(stmt)
        return res.scalars().all()
    
    async def get_by_user_and_name(self, user_id: int, name: str) -> UserCustomTemplate | None:
        """根据用户和名称查询模板"""
        stmt = select(UserCustomTemplate).where(
            and_(
                UserCustomTemplate.user_id == user_id,
                UserCustomTemplate.name == name
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()
    
    async def update(self, template_id: int, **kwargs) -> UserCustomTemplate | None:
        """更新模板"""
        template = await self.get_by_id(template_id)
        if not template:
            return None
        
        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    async def delete(self, template_id: int) -> bool:
        """删除模板"""
        template = await self.get_by_id(template_id)
        if not template:
            return False
        
        await self.db.delete(template)
        await self.db.commit()
        return True
    
    async def get_templates_from_system(self, user_id: int, system_template_id: int) -> Sequence[UserCustomTemplate]:
        """查询用户基于某个系统模板创建的所有模板"""
        stmt = select(UserCustomTemplate).where(
            and_(
                UserCustomTemplate.user_id == user_id,
                UserCustomTemplate.created_from_template_id == system_template_id
            )
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()
