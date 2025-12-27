"""
User API Endpoints
用户相关的 API 端点
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import (
    get_password_hash, 
    verify_password, 
    create_access_token,
    get_current_active_user
)
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, UserUpdate, SendSmsRequest
from app.schemas.response import ApiResponse
from app.services.sms_service import get_sms_service, generate_and_store_code, verify_code, update_sms_log_status
import json
import datetime
from app.core.config import settings
from app.repositories import get_user_repository
from app.repositories.user_repository import UserRepository
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    x_device_type: str | None = Header("web", alias="X-Device-Type"),
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository)
) -> ApiResponse[UserResponse]:
    """
    User registration with anti-fraud protection
    用户注册（需要短信验证码，严格防刷）
    
    Headers:
        X-Device-Type: 设备类型 (web/ios/android/desktop)
    
    防刷机制：
        1. 手机号唯一性检查
        2. 短信验证码验证（必需）
        3. 同一IP每天最多注册5个账号
        4. 同一IP两次注册间隔至少5分钟
        5. User-Agent检测（防止爬虫）
        6. IP黑名单检查
        7. 记录注册审计信息
    
    Returns:
        ApiResponse[UserResponse]: 统一响应格式，data 为用户信息
    """
    # 获取客户端IP和User-Agent
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    device_type = x_device_type or "web"
    
    # ===== 1. 手机号唯一性检查 =====
    if await user_repo.exists_by_phone(user_data.phone):
        logger.warning(
            "registration_phone_exists",
            phone=user_data.phone,
            ip=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号已被注册"
        )

    # ===== 2. 短信验证码验证（强制要求） =====
    if not settings.SMS_PROVIDER:
        logger.warning("sms_provider_not_configured", action="registration_without_sms")
    
    if not user_data.sms_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供短信验证码"
        )
    
    try:
        ok = await verify_code(user_data.phone, user_data.sms_code, purpose="register", db=db)
        if not ok:
            logger.warning(
                "registration_invalid_sms_code",
                phone=user_data.phone,
                ip=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="短信验证码错误或已过期"
            )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # ===== 3. 防刷检查 =====
    from app.services.anti_fraud_service import get_anti_fraud_service
    anti_fraud = get_anti_fraud_service(db)
    
    # 3.1 检查IP注册限制
    if ip_address:
        is_allowed, error_msg = await anti_fraud.check_ip_registration_limit(ip_address)
        if not is_allowed:
            logger.warning(
                "registration_ip_limit_exceeded",
                phone=user_data.phone,
                ip=ip_address,
                reason=error_msg
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_msg
            )
    
    # 3.2 检查User-Agent是否可疑
    if await anti_fraud.check_user_agent_suspicious(user_agent):
        logger.warning(
            "registration_suspicious_user_agent",
            phone=user_data.phone,
            ip=ip_address,
            user_agent=user_agent
        )
        # 可疑UA不直接拒绝，但记录日志供后续分析
        # 如果需要严格控制，可以在这里直接拒绝
    
    # ===== 4. 创建新用户（包含审计信息） =====
    hashed_password = get_password_hash(user_data.password)
    
    # 直接使用SQLAlchemy创建，包含审计字段
    from app.models.user import User
    new_user = User(
        phone=user_data.phone,
        nickname=user_data.nickname,
        hashed_password=hashed_password,
        registration_ip=ip_address,
        registration_user_agent=user_agent,
        registration_source=device_type,
        is_verified=True,  # 通过短信验证即认为已验证
        is_active=True,
        is_banned=False
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # ===== 5. 记录注册事件 =====
    await anti_fraud.record_registration(ip_address or "unknown")
    
    logger.info(
        "user_registered",
        user_id=new_user.id,
        phone=user_data.phone,
        nickname=user_data.nickname,
        registration_ip=ip_address,
        registration_source=device_type,
        user_agent_length=len(user_agent) if user_agent else 0
    )
    
    return ApiResponse[UserResponse].success(data=new_user, message="注册成功")


@router.post("/login", response_model=ApiResponse[Token])
async def login(
    user_data: UserLogin,
    request: Request,
    x_device_type: str | None = Header("web", alias="X-Device-Type"),
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository)
) -> ApiResponse[Token]:
    """
    User login with session management
    用户登录（支持单点登录/互踢机制）
    
    Headers:
        X-Device-Type: 设备类型 (web/ios/android/desktop)
                      同一设备类型只能保持一个活跃会话
                      新登录会自动踢掉该设备类型的旧会话
    
    Returns:
        ApiResponse[Token]: 统一响应格式，data 包含 access_token 和 token_type
        
    Notes:
        - 同一用户可以在不同设备类型同时登录
        - 同一设备类型的新登录会踢掉旧会话
        - 被踢掉的设备会在下次请求时收到401错误
    """
    # 获取客户端IP
    ip_address = request.client.host if request.client else None
    
    # Find user
    user = await user_repo.get_by_phone(user_data.phone)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误"
        )
    
    # 检查账号是否被封禁
    if user.is_banned:
        logger.warning(
            "banned_user_login_attempt",
            user_id=user.id,
            phone=user_data.phone,
            ban_reason=user.ban_reason,
            ip=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"账号已被封禁：{user.ban_reason or '违反用户协议'}"
        )
    
    # 验证登录凭证：密码或验证码
    if user_data.sms_code:
        # 验证码登录
        try:
            ok = await verify_code(user_data.phone, user_data.sms_code, purpose="login", db=db)
            if not ok:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="验证码错误或已过期"
                )
        except RuntimeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    elif user_data.password:
        # 密码登录
        if not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="手机号或密码错误"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供密码或短信验证码"
        )
    
    # 更新最后登录信息
    user.last_login_at = datetime.now()
    user.last_login_ip = ip_address
    await db.commit()
    
    # 验证设备类型
    from typing import cast
    from app.services.session_manager import DeviceType
    
    device_type_str = x_device_type.lower() if x_device_type else "web"
    if device_type_str not in ["web", "ios", "android", "desktop"]:
        device_type_str = "web"
    device_type = cast(DeviceType, device_type_str)
    
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
            # 记录旧会话被踢出事件（安全审计）
            logger.info(
                "session_kicked_out",
                user_id=user.id,
                device_type=device_type,
                old_jti=old_jti[:8] + "...",  # 只记录前8位
                new_jti=jti[:8] + "...",
                phone=user.phone
            )
            
    except RuntimeError as e:
        # Redis未初始化，降级为普通JWT认证
        logger.warning(
            "session_manager_unavailable",
            user_id=user.id,
            device_type=device_type,
            reason=str(e),
            fallback="jwt_only_mode"
        )
    token_data = Token(access_token=access_token, token_type="bearer")
    # 记录登录成功事件（结构化日志）
    logger.info(
        "user_login_success",
        user_id=user.id,
        device_type=device_type,
        jti=jti[:8] + "...",
        phone=user.phone,
        ip=ip_address
    )
    return ApiResponse[Token].success(data=token_data, message="登录成功")


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> ApiResponse[UserResponse]:
    """
    Get current user info
    获取当前用户信息
    
    Returns:
        ApiResponse[UserResponse]: 统一响应格式，data 为当前用户信息
    """
    return ApiResponse[UserResponse].success(data=current_user)



@router.post("/send_sms_code", response_model=ApiResponse[Dict[str, Any]])
async def send_sms_code(
    payload: SendSmsRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[Dict[str, Any]]:
    """
    发送短信验证码（适用于注册/重置密码）
    
    限制：
    - 每个手机号每天最多10次
    - 每个IP每天最多50次
    - 同一手机号60秒内只能发送一次
    
    Body:
        {"phone": "187xxx", "purpose": "register"}
    
    Returns:
        ApiResponse[Dict]: 统一响应格式，data 包含 phone 和 expires_in
    """
    phone = payload.phone
    purpose = payload.purpose or "register"
    
    # 获取客户端IP和User-Agent
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # 生成并存储验证码（包含防刷检查）
    try:
        code, log_id = await generate_and_store_code(
            phone,
            purpose=purpose,
            ip_address=ip_address,
            user_agent=user_agent,
            db=db
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )

    # 发送短信
    sms = get_sms_service()
    sign_name = settings.SMS_SIGN_NAME or settings.APP_NAME
    template_code = settings.SMS_TEMPLATE_CODE or "100001"
    template_param = json.dumps({"code": code, "min": "5"})
    
    try:
        ok = sms.send_sms(phone, sign_name, template_code, template_param)
        
        # 更新数据库日志状态
        if log_id:
            status_str = "sent" if ok else "failed"
            error_msg = None if ok else "短信发送失败"
            await update_sms_log_status(db, log_id, status_str, error_msg)
        
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="短信发送失败"
            )
    except HTTPException:
        raise
    except Exception as e:
        if log_id:
            await update_sms_log_status(db, log_id, "failed", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"短信发送异常: {str(e)}"
        )

    return ApiResponse[Dict[str, Any]].success(
        data={
            "phone": phone,
            "expires_in": settings.SMS_CODE_EXPIRE_SECONDS
        },
        message="验证码已发送"
    )


@router.put("/me", response_model=ApiResponse[UserResponse])
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository)
) -> ApiResponse[UserResponse]:
    """
    Update current user
    更新当前用户信息
    
    Returns:
        ApiResponse[UserResponse]: 统一响应格式，data 为更新后的用户信息
    """
    # Update user fields
    update_fields = user_data.model_dump(exclude_unset=True)
    updated_user = await user_repo.update(current_user, **update_fields)
    
    return ApiResponse[UserResponse].success(data=updated_user, message="更新成功")


@router.post("/logout", response_model=ApiResponse[Dict[str, str]])
async def logout(
    x_device_type: str | None = Header("web", alias="X-Device-Type"),
    current_user: User = Depends(get_current_active_user)
) -> ApiResponse[Dict[str, str]]:
    """
    User logout (single device)
    用户登出（单设备）
    
    Headers:
        X-Device-Type: 要登出的设备类型
        
    Notes:
        - 仅登出当前设备类型的会话
        - 其他设备类型的会话不受影响
    """
    from typing import cast
    from app.services.session_manager import DeviceType
    
    device_type_str = x_device_type.lower() if x_device_type else "web"
    if device_type_str not in ["web", "ios", "android", "desktop"]:
        device_type_str = "web"
    device_type = cast(DeviceType, device_type_str)
    
    try:
        from app.services.session_manager import get_session_manager
        session_manager = get_session_manager()
        
        session_manager.revoke_session(current_user.id, device_type)
        
        return ApiResponse[Dict[str, str]].success(
            data={"device_type": device_type},
            message=f"已登出 {device_type} 设备"
        )
    except RuntimeError:
        # Redis未初始化
        return ApiResponse[Dict[str, str]].success(
            data={"device_type": device_type},
            message="登出成功（会话管理未启用）"
        )


@router.post("/logout/all", response_model=ApiResponse[Dict[str, Any]])
async def logout_all(
    current_user: User = Depends(get_current_active_user)
) -> ApiResponse[Dict[str, Any]]:
    """
    User logout (all devices)
    用户全局登出（所有设备）
    
    Notes:
        - 登出所有设备类型的会话
        - 所有已登录的设备都需要重新登录
    
    Returns:
        ApiResponse[Dict]: 统一响应格式，data 包含 revoked_count
    """
    try:
        from app.services.session_manager import get_session_manager
        session_manager = get_session_manager()
        
        revoked_count = session_manager.revoke_all_sessions(current_user.id)
        
        return ApiResponse[Dict[str, Any]].success(
            data={"revoked_count": revoked_count},
            message=f"已登出所有设备，共 {revoked_count} 个活跃会话"
        )
    except RuntimeError:
        return ApiResponse[Dict[str, Any]].success(
            data={"revoked_count": 0},
            message="登出成功（会话管理未启用）"
        )


@router.get("/sessions", response_model=ApiResponse[Dict[str, Any]])
async def get_active_sessions(
    current_user: User = Depends(get_current_active_user)
) -> ApiResponse[Dict[str, Any]]:
    """
    Get active sessions
    查询当前用户的所有活跃会话
    
    Returns:
        ApiResponse[Dict]: 统一响应格式，data 包含 user_id、active_sessions、total_count
    """
    try:
        from app.services.session_manager import get_session_manager
        session_manager = get_session_manager()
        
        sessions = session_manager.get_active_sessions(current_user.id)
        
        return ApiResponse[Dict[str, Any]].success(
            data={
                "user_id": current_user.id,
                "active_sessions": sessions,
                "total_count": len(sessions)
            }
        )
    except RuntimeError:
        return ApiResponse[Dict[str, Any]].success(
            data={
                "user_id": current_user.id,
                "active_sessions": {},
                "total_count": 0
            },
            message="会话管理未启用"
        )
