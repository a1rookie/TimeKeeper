"""
Family Group Repository
家庭组数据访问层
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.family_group import FamilyGroup
from app.models.family_member import FamilyMember


class FamilyGroupRepository:
    """家庭组数据访问"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, name: str, creator_id: int, description: Optional[str] = None) -> FamilyGroup:
        """创建家庭组"""
        group = FamilyGroup(
            name=name,
            creator_id=creator_id,
            description=description,
            is_active=True
        )
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return group
    
    def get_by_id(self, group_id: int) -> Optional[FamilyGroup]:
        """根据ID查询家庭组"""
        return self.db.query(FamilyGroup).filter(FamilyGroup.id == group_id).first()
    
    def get_by_creator(self, creator_id: int) -> List[FamilyGroup]:
        """查询用户创建的所有家庭组"""
        return self.db.query(FamilyGroup).filter(
            and_(
                FamilyGroup.creator_id == creator_id,
                FamilyGroup.is_active == True
            )
        ).all()
    
    def get_user_groups(self, user_id: int) -> List[FamilyGroup]:
        """查询用户所在的所有家庭组（包括创建和加入的）"""
        return self.db.query(FamilyGroup).join(
            FamilyMember,
            FamilyGroup.id == FamilyMember.group_id
        ).filter(
            and_(
                FamilyMember.user_id == user_id,
                FamilyMember.is_active == True,
                FamilyGroup.is_active == True
            )
        ).all()
    
    def update(self, group_id: int, **kwargs) -> Optional[FamilyGroup]:
        """更新家庭组信息"""
        group = self.get_by_id(group_id)
        if not group:
            return None
        
        for key, value in kwargs.items():
            if hasattr(group, key):
                setattr(group, key, value)
        
        self.db.commit()
        self.db.refresh(group)
        return group
    
    def deactivate(self, group_id: int) -> bool:
        """停用家庭组"""
        group = self.get_by_id(group_id)
        if not group:
            return False
        
        group.is_active = False
        self.db.commit()
        return True
    
    def get_member_count(self, group_id: int) -> int:
        """获取家庭组成员数量"""
        return self.db.query(FamilyMember).filter(
            and_(
                FamilyMember.group_id == group_id,
                FamilyMember.is_active == True
            )
        ).count()
