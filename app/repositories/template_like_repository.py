"""
Template Like Repository
模板点赞数据访问层
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.template_like import TemplateLike


class TemplateLikeRepository:
    """模板点赞数据访问"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_like(self, template_share_id: int, user_id: int) -> Optional[TemplateLike]:
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
        self.db.commit()
        self.db.refresh(like)
        return like
    
    def remove_like(self, template_share_id: int, user_id: int) -> bool:
        """取消点赞"""
        like = self.get_like(template_share_id, user_id)
        if not like:
            return False
        
        self.db.delete(like)
        self.db.commit()
        return True
    
    def get_like(self, template_share_id: int, user_id: int) -> Optional[TemplateLike]:
        """查询用户是否点赞了某个模板"""
        return self.db.query(TemplateLike).filter(
            and_(
                TemplateLike.template_share_id == template_share_id,
                TemplateLike.user_id == user_id
            )
        ).first()
    
    def is_liked(self, template_share_id: int, user_id: int) -> bool:
        """检查用户是否点赞"""
        return self.get_like(template_share_id, user_id) is not None
    
    def get_user_likes(self, user_id: int) -> List[TemplateLike]:
        """获取用户的所有点赞记录"""
        return self.db.query(TemplateLike).filter(
            TemplateLike.user_id == user_id
        ).order_by(TemplateLike.created_at.desc()).all()
    
    def get_template_likes(self, template_share_id: int) -> List[TemplateLike]:
        """获取模板的所有点赞记录"""
        return self.db.query(TemplateLike).filter(
            TemplateLike.template_share_id == template_share_id
        ).all()
    
    def get_like_count(self, template_share_id: int) -> int:
        """获取模板的点赞数量"""
        return self.db.query(TemplateLike).filter(
            TemplateLike.template_share_id == template_share_id
        ).count()
