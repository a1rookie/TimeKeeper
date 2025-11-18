"""
Reminder Template Repository
系统提醒模板数据访问层
"""
from collections.abc import Sequence
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
        description: str | None = None,
        default_recurrence_type: str | None = None,
        default_recurrence_config: dict | None = None,
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
    
    async def get_by_id(self, template_id: int) -> ReminderTemplate | None:
        """根据ID查询模板"""
        result = await self.db.execute(select(ReminderTemplate).where(ReminderTemplate.id == template_id))
        return result.scalar_one_or_none()
    
    async def get_by_category(self, category: str, is_active: bool = True) -> Sequence[ReminderTemplate]:
        """根据分类查询模板"""
        stmt = select(ReminderTemplate).where(ReminderTemplate.category == category)
        if is_active:
            stmt = stmt.where(ReminderTemplate.is_active == True)
        stmt = stmt.order_by(desc(ReminderTemplate.usage_count))
        res = await self.db.execute(stmt)
        return res.scalars().all()
    
    async def get_all_active(self) -> Sequence[ReminderTemplate]:
        """获取所有激活的模板"""
        stmt = select(ReminderTemplate).where(ReminderTemplate.is_active == True).order_by(
            ReminderTemplate.category,
            desc(ReminderTemplate.usage_count)
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()
    
    async def search(self, keyword: str) -> Sequence[ReminderTemplate]:
        """搜索模板"""
        stmt = select(ReminderTemplate).where(
            and_(
                ReminderTemplate.is_active == True,
                or_(
                    ReminderTemplate.name.ilike(f"%{keyword}%"),
                    ReminderTemplate.description.ilike(f"%{keyword}%")
                )
            )
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()
    
    async def get_popular(self, limit: int = 10) -> Sequence[ReminderTemplate]:
        """获取热门模板"""
        stmt = select(ReminderTemplate).where(ReminderTemplate.is_active == True).order_by(desc(ReminderTemplate.usage_count)).limit(limit)
        res = await self.db.execute(stmt)
        return res.scalars().all()
    
    async def increment_usage(self, template_id: int) -> bool:
        """增加使用次数"""
        template = await self.get_by_id(template_id)
        if not template:
            return False

        template.usage_count = (template.usage_count or 0) + 1
        await self.db.commit()
        return True
    
    async def update(self, template_id: int, **kwargs) -> ReminderTemplate | None:
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
    
    async def deactivate(self, template_id: int) -> bool:
        """停用模板"""
        template = await self.get_by_id(template_id)
        if not template:
            return False

        template.is_active = False
        await self.db.commit()
        return True
