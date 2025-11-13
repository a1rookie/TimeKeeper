"""
Family API
家庭共享功能的 API 路由
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.response import ApiResponse

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

@router.post("/groups", response_model=ApiResponse[FamilyGroupDetail], status_code=status.HTTP_201_CREATED)
async def create_family_group(
    data: FamilyGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建家庭组
    - 自动将创建者添加为管理员
    
    Returns:
        ApiResponse[FamilyGroupDetail]: 统一响应格式，data 为家庭组详情
    """
    group_repo = FamilyGroupRepository(db)
    member_repo = FamilyMemberRepository(db)
    
    # 创建家庭组
    group = await group_repo.create(
        name=data.name,
        creator_id=current_user.id,
        description=data.description
    )
    
    # 自动添加创建者为管理员
    await member_repo.add_member(
        group_id=group.id,
        user_id=current_user.id,
        role=MemberRole.ADMIN
    )
    
    # 获取完整信息
    members = await member_repo.get_group_members(group.id)
    
    group_detail = FamilyGroupDetail(
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
    
    return ApiResponse.success(data=group_detail, message="创建成功")


@router.get("/groups", response_model=ApiResponse[List[FamilyGroupResponse]])
async def list_my_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询我的家庭组列表（包括创建的和加入的）
    
    Returns:
        ApiResponse[List[FamilyGroupResponse]]: 统一响应格式，data 为家庭组列表
    """
    group_repo = FamilyGroupRepository(db)
    member_repo = FamilyMemberRepository(db)
    
    groups = await group_repo.get_user_groups(current_user.id)
    
    group_list = []
    for g in groups:
        members = await member_repo.get_group_members(g.id)
        group_list.append(FamilyGroupResponse(
            id=g.id,
            name=g.name,
            description=g.description,
            creator_id=g.creator_id,
            is_active=g.is_active,
            member_count=len(members),
            created_at=g.created_at,
            updated_at=g.updated_at
        ))
    
    return ApiResponse.success(data=group_list)


@router.get("/groups/{group_id}", response_model=ApiResponse[FamilyGroupDetail])
async def get_group_detail(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询家庭组详情（包含成员列表）
    
    Returns:
        ApiResponse[FamilyGroupDetail]: 统一响应格式，data 为家庭组详情
    """
    group_repo = FamilyGroupRepository(db)
    member_repo = FamilyMemberRepository(db)
    
    # 检查家庭组是否存在
    group = await group_repo.get_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="家庭组不存在"
        )
    
    # 检查权限（必须是成员）
    if not await member_repo.is_member(group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该家庭组"
        )
    
    members = await member_repo.get_group_members(group_id)
    
    group_detail = FamilyGroupDetail(
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
    
    return ApiResponse.success(data=group_detail)


@router.put("/groups/{group_id}", response_model=ApiResponse[FamilyGroupResponse])
async def update_group(
    group_id: int,
    data: FamilyGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新家庭组信息（仅管理员可操作）
    
    Returns:
        ApiResponse[FamilyGroupResponse]: 统一响应格式，data 为更新后的家庭组信息
    """
    group_repo = FamilyGroupRepository(db)
    member_repo = FamilyMemberRepository(db)
    
    # 检查权限
    if not await member_repo.is_admin(group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可以修改家庭组信息"
        )
    
    # 更新
    update_data = data.model_dump(exclude_unset=True)
    group = await group_repo.update(group_id, **update_data)
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="家庭组不存在"
        )
    
    members = await member_repo.get_group_members(group_id)
    member_count = len(members)
    
    group_response = FamilyGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        creator_id=group.creator_id,
        is_active=group.is_active,
        member_count=member_count,
        created_at=group.created_at,
        updated_at=group.updated_at
    )
    
    return ApiResponse.success(data=group_response, message="更新成功")


@router.delete("/groups/{group_id}", response_model=ApiResponse[None])
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    停用家庭组（仅创建者可操作）
    
    Returns:
        ApiResponse[None]: 统一响应格式，data 为空
    """
    group_repo = FamilyGroupRepository(db)
    
    group = await group_repo.get_by_id(group_id)
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
    
    await group_repo.deactivate(group_id)
    return ApiResponse.success(message="停用成功")


# ==================== 成员管理 ====================

@router.post("/groups/{group_id}/members", response_model=ApiResponse[FamilyMemberResponse], status_code=status.HTTP_201_CREATED)
async def add_member(
    group_id: int,
    data: FamilyMemberAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    添加成员到家庭组（仅管理员可操作）
    
    Returns:
        ApiResponse[FamilyMemberResponse]: 统一响应格式，data 为添加的成员信息
    """
    group_repo = FamilyGroupRepository(db)
    member_repo = FamilyMemberRepository(db)
    
    # 检查家庭组是否存在
    group = await group_repo.get_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="家庭组不存在"
        )
    
    # 检查权限
    if not await member_repo.is_admin(group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可以添加成员"
        )
    
    # 检查用户是否已经是成员
    if await member_repo.is_member(group_id, data.user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已经是该家庭组成员"
        )
    
    # 添加成员
    member = await member_repo.add_member(
        group_id=group_id,
        user_id=data.user_id,
        role=data.role,
        nickname=data.nickname
    )
    
    member_response = FamilyMemberResponse(
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
    
    return ApiResponse.success(data=member_response, message="添加成功")


@router.put("/groups/{group_id}/members/{member_id}", response_model=ApiResponse[FamilyMemberResponse])
async def update_member(
    group_id: int,
    member_id: int,
    data: FamilyMemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新成员信息（管理员可更新角色，成员可更新自己的昵称）
    
    Returns:
        ApiResponse[FamilyMemberResponse]: 统一响应格式，data 为更新后的成员信息
    """
    member_repo = FamilyMemberRepository(db)
    
    # 检查权限
    target_member = await member_repo.get_by_id(member_id)
    if not target_member or target_member.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="成员不存在"
        )
    
    is_admin = await member_repo.is_admin(group_id, current_user.id)
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
        await member_repo.update_role(member_id, data.role)
    if data.nickname is not None:
        await member_repo.update_nickname(member_id, data.nickname)
    
    # 刷新数据
    updated_member = await member_repo.get_by_id(member_id)
    
    member_response = FamilyMemberResponse(
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
    
    return ApiResponse.success(data=member_response, message="更新成功")


@router.delete("/groups/{group_id}/members/{member_id}", response_model=ApiResponse[None])
async def remove_member(
    group_id: int,
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    移除成员（管理员可移除其他成员，成员可退出）
    
    Returns:
        ApiResponse[None]: 统一响应格式，data 为空
    """
    member_repo = FamilyMemberRepository(db)
    
    target_member = await member_repo.get_by_id(member_id)
    if not target_member or target_member.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="成员不存在"
        )
    
    is_admin = await member_repo.is_admin(group_id, current_user.id)
    is_self = target_member.user_id == current_user.id
    
    # 管理员可移除其他成员，成员可退出
    if not (is_admin or is_self):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权移除该成员"
        )
    
    # 不能移除创建者
    group_repo = FamilyGroupRepository(db)
    group = await group_repo.get_by_id(group_id)
    if target_member.user_id == group.creator_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能移除家庭组创建者"
        )
    
    await member_repo.remove_member(group_id, target_member.user_id)
    return ApiResponse.success(message="移除成功")
