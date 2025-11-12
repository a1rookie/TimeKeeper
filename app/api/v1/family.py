"""
Family API
家庭共享功能的 API 路由
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.family_member import MemberRole
from app.schemas.family import (
    FamilyGroupCreate,
    FamilyGroupUpdate,
    FamilyGroupResponse,
    FamilyGroupDetail,
    FamilyMemberAdd,
    FamilyMemberUpdate,
    FamilyMemberResponse
)
from app.repositories.family_group_repository import FamilyGroupRepository
from app.repositories.family_member_repository import FamilyMemberRepository

router = APIRouter()


# ==================== 家庭组管理 ====================

@router.post("/groups", response_model=FamilyGroupDetail, status_code=status.HTTP_201_CREATED)
def create_family_group(
    data: FamilyGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建家庭组
    - 自动将创建者添加为管理员
    """
    group_repo = FamilyGroupRepository(db)
    member_repo = FamilyMemberRepository(db)
    
    # 创建家庭组
    group = group_repo.create(
        name=data.name,
        creator_id=current_user.id,
        description=data.description
    )
    
    # 自动添加创建者为管理员
    member_repo.add_member(
        group_id=group.id,
        user_id=current_user.id,
        role=MemberRole.ADMIN
    )
    
    # 获取完整信息
    members = member_repo.get_group_members(group.id)
    
    return FamilyGroupDetail(
        id=group.id,
        name=group.name,
        description=group.description,
        creator_id=group.creator_id,
        is_active=group.is_active,
        member_count=len(members),
        created_at=group.created_at,
        updated_at=group.updated_at,
        members=[
            FamilyMemberResponse(
                id=m.id,
                group_id=m.group_id,
                user_id=m.user_id,
                role=m.role,
                nickname=m.nickname,
                is_active=m.is_active,
                joined_at=m.joined_at,
                user_phone=m.user.phone if m.user else None,
                user_nickname=m.user.nickname if m.user else None
            ) for m in members
        ]
    )


@router.get("/groups", response_model=List[FamilyGroupResponse])
def list_my_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询我的家庭组列表（包括创建的和加入的）
    """
    group_repo = FamilyGroupRepository(db)
    member_repo = FamilyMemberRepository(db)
    
    groups = group_repo.get_user_groups(current_user.id)
    
    return [
        FamilyGroupResponse(
            id=g.id,
            name=g.name,
            description=g.description,
            creator_id=g.creator_id,
            is_active=g.is_active,
            member_count=member_repo.get_group_members(g.id).__len__(),
            created_at=g.created_at,
            updated_at=g.updated_at
        ) for g in groups
    ]


@router.get("/groups/{group_id}", response_model=FamilyGroupDetail)
def get_group_detail(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询家庭组详情（包含成员列表）
    """
    group_repo = FamilyGroupRepository(db)
    member_repo = FamilyMemberRepository(db)
    
    # 检查家庭组是否存在
    group = group_repo.get_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="家庭组不存在"
        )
    
    # 检查权限（必须是成员）
    if not member_repo.is_member(group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该家庭组"
        )
    
    members = member_repo.get_group_members(group_id)
    
    return FamilyGroupDetail(
        id=group.id,
        name=group.name,
        description=group.description,
        creator_id=group.creator_id,
        is_active=group.is_active,
        member_count=len(members),
        created_at=group.created_at,
        updated_at=group.updated_at,
        members=[
            FamilyMemberResponse(
                id=m.id,
                group_id=m.group_id,
                user_id=m.user_id,
                role=m.role,
                nickname=m.nickname,
                is_active=m.is_active,
                joined_at=m.joined_at,
                user_phone=m.user.phone if m.user else None,
                user_nickname=m.user.nickname if m.user else None
            ) for m in members
        ]
    )


@router.put("/groups/{group_id}", response_model=FamilyGroupResponse)
def update_group(
    group_id: int,
    data: FamilyGroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新家庭组信息（仅管理员可操作）
    """
    group_repo = FamilyGroupRepository(db)
    member_repo = FamilyMemberRepository(db)
    
    # 检查权限
    if not member_repo.is_admin(group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可以修改家庭组信息"
        )
    
    # 更新
    update_data = data.model_dump(exclude_unset=True)
    group = group_repo.update(group_id, **update_data)
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="家庭组不存在"
        )
    
    member_count = member_repo.get_group_members(group_id).__len__()
    
    return FamilyGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        creator_id=group.creator_id,
        is_active=group.is_active,
        member_count=member_count,
        created_at=group.created_at,
        updated_at=group.updated_at
    )


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    停用家庭组（仅创建者可操作）
    """
    group_repo = FamilyGroupRepository(db)
    
    group = group_repo.get_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="家庭组不存在"
        )
    
    # 仅创建者可以停用
    if group.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅创建者可以停用家庭组"
        )
    
    group_repo.deactivate(group_id)
    return None


# ==================== 成员管理 ====================

@router.post("/groups/{group_id}/members", response_model=FamilyMemberResponse, status_code=status.HTTP_201_CREATED)
def add_member(
    group_id: int,
    data: FamilyMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    添加成员到家庭组（仅管理员可操作）
    """
    group_repo = FamilyGroupRepository(db)
    member_repo = FamilyMemberRepository(db)
    
    # 检查家庭组是否存在
    group = group_repo.get_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="家庭组不存在"
        )
    
    # 检查权限
    if not member_repo.is_admin(group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可以添加成员"
        )
    
    # 检查用户是否已经是成员
    if member_repo.is_member(group_id, data.user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已经是该家庭组成员"
        )
    
    # 添加成员
    member = member_repo.add_member(
        group_id=group_id,
        user_id=data.user_id,
        role=data.role,
        nickname=data.nickname
    )
    
    return FamilyMemberResponse(
        id=member.id,
        group_id=member.group_id,
        user_id=member.user_id,
        role=member.role,
        nickname=member.nickname,
        is_active=member.is_active,
        joined_at=member.joined_at,
        user_phone=member.user.phone if member.user else None,
        user_nickname=member.user.nickname if member.user else None
    )


@router.put("/groups/{group_id}/members/{member_id}", response_model=FamilyMemberResponse)
def update_member(
    group_id: int,
    member_id: int,
    data: FamilyMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新成员信息（管理员可更新角色，成员可更新自己的昵称）
    """
    member_repo = FamilyMemberRepository(db)
    
    # 检查权限
    target_member = member_repo.get_by_id(member_id)
    if not target_member or target_member.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="成员不存在"
        )
    
    is_admin = member_repo.is_admin(group_id, current_user.id)
    is_self = target_member.user_id == current_user.id
    
    # 更新角色需要管理员权限
    if data.role is not None and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可以修改成员角色"
        )
    
    # 更新昵称：管理员或本人
    if data.nickname is not None and not (is_admin or is_self):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改该成员昵称"
        )
    
    # 执行更新
    if data.role is not None:
        member_repo.update_role(member_id, data.role)
    if data.nickname is not None:
        member_repo.update_nickname(member_id, data.nickname)
    
    # 刷新数据
    updated_member = member_repo.get_by_id(member_id)
    
    return FamilyMemberResponse(
        id=updated_member.id,
        group_id=updated_member.group_id,
        user_id=updated_member.user_id,
        role=updated_member.role,
        nickname=updated_member.nickname,
        is_active=updated_member.is_active,
        joined_at=updated_member.joined_at,
        user_phone=updated_member.user.phone if updated_member.user else None,
        user_nickname=updated_member.user.nickname if updated_member.user else None
    )


@router.delete("/groups/{group_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    group_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    移除成员（管理员可移除其他成员，成员可退出）
    """
    member_repo = FamilyMemberRepository(db)
    
    target_member = member_repo.get_by_id(member_id)
    if not target_member or target_member.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="成员不存在"
        )
    
    is_admin = member_repo.is_admin(group_id, current_user.id)
    is_self = target_member.user_id == current_user.id
    
    # 管理员可移除其他成员，成员可退出
    if not (is_admin or is_self):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权移除该成员"
        )
    
    # 不能移除创建者
    group_repo = FamilyGroupRepository(db)
    group = group_repo.get_by_id(group_id)
    if target_member.user_id == group.creator_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能移除家庭组创建者"
        )
    
    member_repo.remove_member(group_id, target_member.user_id)
    return None
