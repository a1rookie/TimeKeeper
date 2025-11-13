"""
Reminder Template Repository
系统提醒模板数据访问层
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import and_, or_, desc
from app.models.reminder_template import ReminderTemplate


class ReminderTemplateRepository:
    """系统模板数据访问"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        name: str,
        category: str,
        description: Optional[str] = None,
        default_recurrence_type: Optional[str] = None,
        default_recurrence_config: Optional[dict] = None,
        default_remind_advance_days: int = 0
    ) -> ReminderTemplate:
        """创建系统模板"""
        template = ReminderTemplate(
            name=name,
            category=category,
            description=description,
            default_recurrence_type=default_recurrence_type,
            default_recurrence_config=default_recurrence_config,
            default_remind_advance_days=default_remind_advance_days,
            is_active=True,
            usage_count=0
        )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    async def get_by_id(self, template_id: int) -> Optional[ReminderTemplate]:
        """根据ID查询模板"""
        result = await self.db.execute(select(ReminderTemplate).filter(
            ReminderTemplate.id == template_id
        ))
        return result.scalar_one_or_none()
    
    async def get_by_category(self, category: str, is_active: bool = True) -> List[ReminderTemplate]:
        """根据分类查询模板"""
        query = self.db.query(ReminderTemplate).filter(
            ReminderTemplate.category == category
        )
        if is_active:
            query = query.filter(ReminderTemplate.is_active == True)
        return query.order_by(desc(ReminderTemplate.usage_count)).all()
    
    async def get_all_active(self) -> List[ReminderTemplate]:
        """获取所有激活的模板"""
        return self.db.query(ReminderTemplate).filter(
            ReminderTemplate.is_active == True
        ).order_by(
            ReminderTemplate.category,
            desc(ReminderTemplate.usage_count)
        ).all()
    
    async def search(self, keyword: str) -> List[ReminderTemplate]:
        """搜索模板"""
        return self.db.query(ReminderTemplate).filter(
            and_(
                ReminderTemplate.is_active == True,
                or_(
                    ReminderTemplate.name.ilike(f"%{keyword}%"),
                    ReminderTemplate.description.ilike(f"%{keyword}%")
                )
            )
        ).all()
    
    async def get_popular(self, limit: int = 10) -> List[ReminderTemplate]:
        """获取热门模板"""
        return self.db.query(ReminderTemplate).filter(
            ReminderTemplate.is_active == True
        ).order_by(desc(ReminderTemplate.usage_count)).limit(limit).all()
    
    async def increment_usage(self, template_id: int) -> bool:
        """增加使用次数"""
        template = self.get_by_id(template_id)
        if not template:
            return False
        
        template.usage_count += 1
        await self.db.commit()
        return True
    
    async def update(self, template_id: int, **kwargs) -> Optional[ReminderTemplate]:
        """更新模板"""
        template = self.get_by_id(template_id)
        if not template:
            return None
        
        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    async def deactivate(self, template_id: int) -> bool:
        """停用模板"""
        template = self.get_by_id(template_id)
        if not template:
            return False
        
        template.is_active = False
        await self.db.commit()
        return True
