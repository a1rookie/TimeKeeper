"""
Admin User Management API
管理员用户管理接口
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.response import ApiResponse
from app.core.permissions import get_current_super_admin_user
from app.repositories import get_user_repository
from app.repositories.user_repository import UserRepository
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/admin/users", tags=["Admin - User Management"])


@router.post("/{user_id}/set-role", response_model=ApiResponse[Dict[str, Any]])
async def set_user_role(
    user_id: int,
    role: UserRole = Query(..., description="要设置的角色"),
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    current_user: User = Depends(get_current_super_admin_user)
) -> ApiResponse[Dict[str, Any]]:
    """
    设置用户角色（仅超级管理员）
    
    角色说明：
    - user: 普通用户
    - admin: 管理员（可管理用户、查看统计）
    - super_admin: 超级管理员（可设置其他管理员）
    """
    # 不能修改自己的角色
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的角色"
        )
    
    target_user = await user_repo.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    old_role = target_user.role
    target_user.role = role
    
    await db.commit()
    await db.refresh(target_user)
    
    logger.warning(
        "admin_user_role_changed",
        target_user_id=user_id,
        target_phone=target_user.phone,
        old_role=old_role.value,
        new_role=role.value,
        operator=current_user.id
    )
    
    return ApiResponse[Dict[str, Any]].success(
        data={
            "user_id": user_id,
            "phone": target_user.phone,
            "old_role": old_role.value,
            "new_role": role.value
        },
        message=f"用户角色已更新为 {role.value}"
    )


@router.get("/list-admins", response_model=ApiResponse[List[Dict[str, Any]]])
async def list_admin_users(
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    current_user: User = Depends(get_current_super_admin_user)
) -> ApiResponse[List[Dict[str, Any]]]:
    """
    查看所有管理员用户（仅超级管理员）
    """
    # 这里需要在Repository中添加查询方法
    from sqlalchemy import select
    result = await db.execute(
        select(User).where(
            User.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN])
        )
    )
    admins = result.scalars().all()
    
    admin_list = [
        {
            "user_id": admin.id,
            "phone": admin.phone,
            "nickname": admin.nickname,
            "role": admin.role.value,
            "is_active": admin.is_active,
            "created_at": admin.created_at.isoformat()
        }
        for admin in admins
    ]
    
    return ApiResponse[List[Dict[str, Any]]].success(
        data=admin_list,
        message=f"共 {len(admin_list)} 位管理员"
    )
