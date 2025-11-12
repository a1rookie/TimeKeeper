"""
Family Member Repository
家庭成员数据访问层
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.family_member import FamilyMember, MemberRole


class FamilyMemberRepository:
    """家庭成员数据访问"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_member(
        self,
        group_id: int,
        user_id: int,
        role: MemberRole = MemberRole.MEMBER,
        nickname: Optional[str] = None
    ) -> FamilyMember:
        """添加成员到家庭组"""
        member = FamilyMember(
            group_id=group_id,
            user_id=user_id,
            role=role,
            nickname=nickname,
            is_active=True
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member
    
    def get_by_id(self, member_id: int) -> Optional[FamilyMember]:
        """根据ID查询成员"""
        return self.db.query(FamilyMember).filter(FamilyMember.id == member_id).first()
    
    def get_member(self, group_id: int, user_id: int) -> Optional[FamilyMember]:
        """查询指定用户在家庭组中的成员信息"""
        return self.db.query(FamilyMember).filter(
            and_(
                FamilyMember.group_id == group_id,
                FamilyMember.user_id == user_id,
                FamilyMember.is_active == True
            )
        ).first()
    
    def get_group_members(self, group_id: int) -> List[FamilyMember]:
        """查询家庭组所有成员"""
        return self.db.query(FamilyMember).filter(
            and_(
                FamilyMember.group_id == group_id,
                FamilyMember.is_active == True
            )
        ).all()
    
    def is_member(self, group_id: int, user_id: int) -> bool:
        """检查用户是否为家庭组成员"""
        return self.get_member(group_id, user_id) is not None
    
    def is_admin(self, group_id: int, user_id: int) -> bool:
        """检查用户是否为管理员"""
        member = self.get_member(group_id, user_id)
        return member is not None and member.role == MemberRole.ADMIN
    
    def update_role(self, member_id: int, role: MemberRole) -> Optional[FamilyMember]:
        """更新成员角色"""
        member = self.get_by_id(member_id)
        if not member:
            return None
        
        member.role = role
        self.db.commit()
        self.db.refresh(member)
        return member
    
    def update_nickname(self, member_id: int, nickname: str) -> Optional[FamilyMember]:
        """更新成员昵称"""
        member = self.get_by_id(member_id)
        if not member:
            return None
        
        member.nickname = nickname
        self.db.commit()
        self.db.refresh(member)
        return member
    
    def remove_member(self, group_id: int, user_id: int) -> bool:
        """移除成员"""
        member = self.get_member(group_id, user_id)
        if not member:
            return False
        
        member.is_active = False
        self.db.commit()
        return True
    
    def get_user_groups_count(self, user_id: int) -> int:
        """获取用户加入的家庭组数量"""
        return self.db.query(FamilyMember).filter(
            and_(
                FamilyMember.user_id == user_id,
                FamilyMember.is_active == True
            )
        ).count()
