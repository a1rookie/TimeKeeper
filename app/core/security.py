"""
Security Utilities
安全工具：密码哈希、JWT 令牌生成等
"""

from datetime import UTC, datetime
from datetime import datetime, timedelta
from typing import Any, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from typing import Literal, cast

# 设备类型定义
DeviceType = Literal["web", "ios", "android", "desktop"]


def to_device_type(s: str) -> DeviceType:
    if s not in ("web", "ios", "android", "desktop"):
        raise ValueError("invalid device_type")
    return cast(DeviceType, s)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash using bcrypt directly"""
    # Truncate password to 72 bytes
    password_bytes = plain_password.encode('utf-8')[:72]
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hash_bytes)


def get_password_hash(password: str) -> str:
    """Generate password hash using bcrypt directly"""
    # Truncate password to 72 bytes
    password_bytes = password.encode('utf-8')[:72]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))
    return hashed.decode('utf-8')


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    device_type: str = "web"
) -> tuple[str, str]:
    """
    Create JWT access token
    创建 JWT 访问令牌
    
    Args:
        data: Token payload data
        expires_delta: Custom expiration time
        device_type: Device type (web/ios/android/desktop)
        
    Returns:
        Tuple of (token, jti)
    """
    import uuid
    
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 生成唯一的 JTI (JWT ID)
    jti = str(uuid.uuid4())
    
    to_encode.update({
        "exp": expire,
        "jti": jti,
        "device_type": device_type,
        "iat": datetime.now(UTC)
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt, jti


def verify_token(token: str) -> Optional[dict]:
    """
    Verify JWT token and return payload
    验证 JWT 令牌并返回载荷
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user from JWT token
    从 JWT 令牌获取当前认证用户 - 异步版本
    
    验证流程：
    1. 解析JWT token
    2. 检查token是否在黑名单（被踢出）
    3. 检查是否为当前设备的活跃会话
    4. 从数据库获取用户信息
    
    Args:
        credentials: HTTP Authorization header with Bearer token
        db: Async database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: 401 if token is invalid, revoked, or session is inactive
    """
    # Import here to avoid circular dependency
    from app.repositories.user_repository import UserRepository
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    session_expired_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="会话已过期或在其他设备登录，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    
    try:
        payload: dict[str, Any] = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int | None = payload.get("user_id")
        jti: str | None = payload.get("jti")
        device_type: DeviceType = to_device_type(payload.get("device_type", "web"))
        
        if user_id is None or jti is None:
            raise credentials_exception
        
        # 检查会话状态（如果Redis可用）
        try:
            from app.services.session_manager import get_session_manager
            session_manager = get_session_manager()
            
            # 1. 检查token是否在黑名单
            if session_manager.is_token_blacklisted(jti):
                raise session_expired_exception
            
            # 2. 检查是否为活跃会话（是否被其他登录踢出）
            if not session_manager.is_active_session(user_id, device_type, jti):
                raise session_expired_exception
            
            # 3. 可选：延长会话（用户活跃则自动续期）
            # session_manager.extend_session(user_id, device_type)
            
        except RuntimeError:
            # Redis未初始化，跳过会话检查（降级为仅JWT验证）
            pass
            
    except JWTError:
        raise credentials_exception
    
    # Get user from database using Repository
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """
    Get current active user
    获取当前活跃用户（未来可添加用户状态检查）
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object
        
    Raises:
        HTTPException: 400 if user is inactive
    """
    # 未来可以添加用户状态检查
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="用户未激活")
    
    return current_user
