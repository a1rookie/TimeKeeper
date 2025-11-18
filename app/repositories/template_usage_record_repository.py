"""
Template Usage Record Repository
模板使用记录数据访问层
"""
from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import and_, desc
from app.models.template_usage_record import TemplateUsageRecord


class TemplateUsageRecordRepository:
    """模板使用记录数据访问"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        template_share_id: int,
        user_id: int,
        feedback_rating: int | None = None,
        feedback_comment: str | None = None
    ) -> TemplateUsageRecord:
        """创建使用记录"""
        record = TemplateUsageRecord(
            template_share_id=template_share_id,
            user_id=user_id,
            feedback_rating=feedback_rating,
            feedback_comment=feedback_comment
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record
    
    async def get_by_id(self, record_id: int) -> TemplateUsageRecord | None:
        """根据ID查询记录"""
        result = await self.db.execute(select(TemplateUsageRecord).filter(
            TemplateUsageRecord.id == record_id
        ))
        return result.scalar_one_or_none()
    
    async def get_by_share(self, template_share_id: int) -> Sequence[TemplateUsageRecord]:
        """查询模板分享的所有使用记录"""
        stmt = select(TemplateUsageRecord).where(
            TemplateUsageRecord.template_share_id == template_share_id
        ).order_by(desc(TemplateUsageRecord.used_at))
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_by_user(self, user_id: int) -> Sequence[TemplateUsageRecord]:
        """查询用户的使用记录"""
        stmt = select(TemplateUsageRecord).where(
            TemplateUsageRecord.user_id == user_id
        ).order_by(desc(TemplateUsageRecord.used_at))
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def check_existing(self, template_share_id: int, user_id: int) -> TemplateUsageRecord | None:
        """检查用户是否已使用过该模板"""
        stmt = select(TemplateUsageRecord).where(
            and_(
                TemplateUsageRecord.template_share_id == template_share_id,
                TemplateUsageRecord.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_feedback(
        self,
        record_id: int,
        feedback_rating: int | None = None,
        feedback_comment: str | None = None
    ) -> TemplateUsageRecord | None:
        """更新反馈"""
        record = await self.get_by_id(record_id)
        if not record:
            return None
        
        if feedback_rating is not None:
            record.feedback_rating = feedback_rating
        if feedback_comment is not None:
            record.feedback_comment = feedback_comment
        
        await self.db.commit()
        await self.db.refresh(record)
        return record
    
    async def get_avg_rating(self, template_share_id: int) -> float:
        """计算模板的平均评分"""
        from sqlalchemy import func
        
        stmt = select(
            func.avg(TemplateUsageRecord.feedback_rating)
        ).where(
            and_(
                TemplateUsageRecord.template_share_id == template_share_id,
                TemplateUsageRecord.feedback_rating.isnot(None)
            )
        )
        result = await self.db.execute(stmt)
        avg_value = result.scalar()
        
        return round(float(avg_value), 2) if avg_value else 0.0
