"""
User API Endpoints
用户相关的 API 端点
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from app.core.security import (
    get_password_hash, 
    verify_password, 
    create_access_token,
    get_current_active_user
)
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, UserUpdate
from app.repositories import get_user_repository
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate, 
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    User registration
    用户注册
    """
    # Check if user exists
    if user_repo.exists_by_phone(user_data.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号已被注册"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = user_repo.create(
        phone=user_data.phone,
        nickname=user_data.nickname,
        hashed_password=hashed_password
    )
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    x_device_type: Optional[str] = Header("web", alias="X-Device-Type"),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    User login with session management
    用户登录（支持单点登录/互踢机制）
    
    Headers:
        X-Device-Type: 设备类型 (web/ios/android/desktop)
                      同一设备类型只能保持一个活跃会话
                      新登录会自动踢掉该设备类型的旧会话
    
    Returns:
        Token: JWT访问令牌
        
    Notes:
        - 同一用户可以在不同设备类型同时登录
        - 同一设备类型的新登录会踢掉旧会话
        - 被踢掉的设备会在下次请求时收到401错误
    """
    # Find user
    user = user_repo.get_by_phone(user_data.phone)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误"
        )
    
    # Verify password
    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误"
        )
    
    # 验证设备类型
    device_type = x_device_type.lower()
    if device_type not in ["web", "ios", "android", "desktop"]:
        device_type = "web"
    
    # Create access token with JTI
    access_token, jti = create_access_token(
        data={"user_id": user.id},
        device_type=device_type
    )
    
    # 管理会话（如果Redis可用）
    try:
        from app.services.session_manager import get_session_manager
        session_manager = get_session_manager()
        
        # 创建新会话，踢掉同设备类型的旧会话
        old_jti = session_manager.create_session(
            user_id=user.id,
            device_type=device_type,
            jti=jti,
            kick_previous=True
        )
        
        if old_jti:
            # 可以记录日志：旧会话被踢出
            pass
            
    except RuntimeError:
        # Redis未初始化，降级为普通JWT认证
        pass
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user info
    获取当前用户信息
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Update current user
    更新当前用户信息
    """
    # Update user fields
    update_fields = user_data.model_dump(exclude_unset=True)
    updated_user = user_repo.update(current_user, **update_fields)
    
    return updated_user


@router.post("/logout")
async def logout(
    x_device_type: Optional[str] = Header("web", alias="X-Device-Type"),
    current_user: User = Depends(get_current_active_user)
):
    """
    User logout (single device)
    用户登出（单设备）
    
    Headers:
        X-Device-Type: 要登出的设备类型
        
    Notes:
        - 仅登出当前设备类型的会话
        - 其他设备类型的会话不受影响
    """
    device_type = x_device_type.lower()
    if device_type not in ["web", "ios", "android", "desktop"]:
        device_type = "web"
    
    try:
        from app.services.session_manager import get_session_manager
        session_manager = get_session_manager()
        
        session_manager.revoke_session(current_user.id, device_type)
        
        return {"message": f"已登出 {device_type} 设备"}
    except RuntimeError:
        # Redis未初始化
        return {"message": "登出成功（会话管理未启用）"}


@router.post("/logout/all")
async def logout_all(
    current_user: User = Depends(get_current_active_user)
):
    """
    User logout (all devices)
    用户全局登出（所有设备）
    
    Notes:
        - 登出所有设备类型的会话
        - 所有已登录的设备都需要重新登录
    """
    try:
        from app.services.session_manager import get_session_manager
        session_manager = get_session_manager()
        
        revoked_count = session_manager.revoke_all_sessions(current_user.id)
        
        return {"message": f"已登出所有设备，共 {revoked_count} 个活跃会话"}
    except RuntimeError:
        return {"message": "登出成功（会话管理未启用）"}


@router.get("/sessions")
async def get_active_sessions(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get active sessions
    查询当前用户的所有活跃会话
    
    Returns:
        所有设备类型的活跃会话信息
    """
    try:
        from app.services.session_manager import get_session_manager
        session_manager = get_session_manager()
        
        sessions = session_manager.get_active_sessions(current_user.id)
        
        return {
            "user_id": current_user.id,
            "active_sessions": sessions,
            "total_count": len(sessions)
        }
    except RuntimeError:
        return {
            "user_id": current_user.id,
            "active_sessions": {},
            "total_count": 0,
            "message": "会话管理未启用"
        }
