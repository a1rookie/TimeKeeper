"""
Permission Dependencies
权限验证依赖
"""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from app.models.user import User, UserRole
from app.core.security import get_current_active_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    获取当前管理员用户
    
    要求：用户角色为 admin 或 super_admin
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def get_current_super_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    获取当前超级管理员用户
    
    要求：用户角色为 super_admin
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    return current_user


def check_permission(required_role: UserRole):
    """
    权限检查装饰器工厂
    
    使用方式:
    @router.get("/admin-only")
    async def admin_endpoint(
        current_user: User = Depends(check_permission(UserRole.ADMIN))
    ):
        ...
    """
    async def permission_checker(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        if current_user.role == UserRole.SUPER_ADMIN:
            # 超级管理员拥有所有权限
            return current_user
        
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 {required_role.value} 权限"
            )
        return current_user
    
    return permission_checker
