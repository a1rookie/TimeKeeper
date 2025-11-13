"""
Template Usage Record Repository
模板使用记录数据访问层
"""
from typing import List, Optional
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
        feedback_rating: Optional[int] = None,
        feedback_comment: Optional[str] = None
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
    
    async def get_by_id(self, record_id: int) -> Optional[TemplateUsageRecord]:
        """根据ID查询记录"""
        result = await self.db.execute(select(TemplateUsageRecord).filter(
            TemplateUsageRecord.id == record_id
        ))
        return result.scalar_one_or_none()
    
    async def get_by_share(self, template_share_id: int) -> List[TemplateUsageRecord]:
        """查询模板分享的所有使用记录"""
        return self.db.query(TemplateUsageRecord).filter(
            TemplateUsageRecord.template_share_id == template_share_id
        ).order_by(desc(TemplateUsageRecord.used_at)).all()
    
    async def get_by_user(self, user_id: int) -> List[TemplateUsageRecord]:
        """查询用户的使用记录"""
        return self.db.query(TemplateUsageRecord).filter(
            TemplateUsageRecord.user_id == user_id
        ).order_by(desc(TemplateUsageRecord.used_at)).all()
    
    async def check_existing(self, template_share_id: int, user_id: int) -> Optional[TemplateUsageRecord]:
        """检查用户是否已使用过该模板"""
        return self.db.query(TemplateUsageRecord).filter(
            and_(
                TemplateUsageRecord.template_share_id == template_share_id,
                TemplateUsageRecord.user_id == user_id
            )
        ).first()
    
    async def update_feedback(
        self,
        record_id: int,
        feedback_rating: Optional[int] = None,
        feedback_comment: Optional[str] = None
    ) -> Optional[TemplateUsageRecord]:
        """更新反馈"""
        record = self.get_by_id(record_id)
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
        
        result = self.db.query(
            func.avg(TemplateUsageRecord.feedback_rating)
        ).filter(
            and_(
                TemplateUsageRecord.template_share_id == template_share_id,
                TemplateUsageRecord.feedback_rating.isnot(None)
            )
        ).scalar()
        
        return round(float(result), 2) if result else 0.0
