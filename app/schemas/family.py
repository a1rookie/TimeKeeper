"""
Family Group Schemas
家庭组相关的 Pydantic 模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.family_member import MemberRole


# 创建家庭组
class FamilyGroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="家庭组名称")
    description: Optional[str] = Field(None, max_length=200, description="家庭组描述")


# 更新家庭组
class FamilyGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None


# 家庭组响应
class FamilyGroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    creator_id: int
    is_active: bool
    member_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 添加成员
class FamilyMemberAdd(BaseModel):
    user_id: int = Field(..., description="用户ID")
    role: MemberRole = Field(MemberRole.MEMBER, description="成员角色")
    nickname: Optional[str] = Field(None, max_length=50, description="在家庭组中的昵称")


# 更新成员
class FamilyMemberUpdate(BaseModel):
    role: Optional[MemberRole] = None
    nickname: Optional[str] = Field(None, max_length=50)


# 成员响应
class FamilyMemberResponse(BaseModel):
    id: int
    group_id: int
    user_id: int
    role: MemberRole
    nickname: Optional[str]
    is_active: bool
    joined_at: datetime
    # 关联的用户信息
    user_phone: Optional[str] = None
    user_nickname: Optional[str] = None

    class Config:
        from_attributes = True


# 家庭组详情（包含成员列表）
class FamilyGroupDetail(FamilyGroupResponse):
    members: List[FamilyMemberResponse] = []

    class Config:
        from_attributes = True
