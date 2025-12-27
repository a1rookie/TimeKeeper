"""
Admin API - Anti-Fraud Management
管理员API - 防刷管理

功能：
1. 查看IP注册统计
2. IP黑名单管理
3. 用户封禁管理
4. 注册审计日志
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.response import ApiResponse
from app.services.anti_fraud_service import get_anti_fraud_service
from app.core.permissions import get_current_admin_user
from app.repositories import get_user_repository
from app.repositories.user_repository import UserRepository
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/admin/anti-fraud", tags=["Admin - Anti-Fraud"])


@router.get("/ip-stats/{ip_address}", response_model=ApiResponse[Dict[str, Any]])
async def get_ip_registration_stats(
    ip_address: str,
    days: int = Query(7, ge=1, le=90, description="统计最近N天"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> ApiResponse[Dict[str, Any]]:
    """
    查看指定IP的注册统计
    
    返回：
    - 总注册数
    - 今日注册数
    - 最近N天注册数
    - 是否在黑名单
    - 最近注册的用户列表
    """
    anti_fraud = get_anti_fraud_service(db)
    stats = await anti_fraud.get_registration_stats_by_ip(ip_address, days)
    
    return ApiResponse[Dict[str, Any]].success(data=stats)


@router.get("/suspicious-ips", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_suspicious_ips(
    days: int = Query(7, ge=1, le=30, description="最近N天"),
    min_registrations: int = Query(3, ge=2, le=100, description="最少注册数"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    current_user: User = Depends(get_current_admin_user)
) -> ApiResponse[List[Dict[str, Any]]]:
    """
    查询可疑IP列表
    
    可疑标准：
    - 最近N天注册次数超过阈值
    - 按注册数量降序排列
    """
    # 使用Repository获取数据
    suspicious_ips_data = await user_repo.get_suspicious_ips(
        days=days,
        min_registrations=min_registrations,
        limit=limit
    )
    
    # 补充黑名单状态
    anti_fraud = get_anti_fraud_service(db)
    for ip_data in suspicious_ips_data:
        is_blacklisted = await anti_fraud.is_ip_blacklisted(ip_data["ip"])
        ip_data["is_blacklisted"] = is_blacklisted
        # 计算时间跨度
        first_reg = ip_data["first_registration"]
        last_reg = ip_data["last_registration"]
        ip_data["days_span"] = (last_reg - first_reg).days
        # 转换为ISO格式
        ip_data["last_registration"] = last_reg.isoformat()
        ip_data["first_registration"] = first_reg.isoformat()
    
    return ApiResponse[List[Dict[str, Any]]].success(
        data=suspicious_ips_data,
        message=f"找到 {len(suspicious_ips_data)} 个可疑IP"
    )


@router.post("/blacklist/add", response_model=ApiResponse[Dict[str, str]])
async def add_ip_to_blacklist(
    ip_address: str = Query(..., description="要封禁的IP地址"),
    reason: str = Query(..., description="封禁原因"),
    duration_hours: int = Query(24, ge=0, le=8760, description="封禁时长（小时），0表示永久"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> ApiResponse[Dict[str, str]]:
    """
    将IP加入黑名单
    
    参数：
    - ip_address: IP地址
    - reason: 封禁原因
    - duration_hours: 封禁时长（小时），0表示永久封禁
    """
    anti_fraud = get_anti_fraud_service(db)
    await anti_fraud.add_ip_to_blacklist(ip_address, reason, duration_hours)
    
    logger.warning(
        "admin_ip_blacklisted",
        ip=ip_address,
        reason=reason,
        duration_hours=duration_hours,
        operator=current_user.id
    )
    
    return ApiResponse[Dict[str, str]].success(
        data={
            "ip": ip_address,
            "reason": reason,
            "duration": f"{duration_hours}小时" if duration_hours > 0 else "永久"
        },
        message="IP已加入黑名单"
    )


@router.delete("/blacklist/remove", response_model=ApiResponse[Dict[str, str]])
async def remove_ip_from_blacklist(
    ip_address: str = Query(..., description="要解封的IP地址"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> ApiResponse[Dict[str, str]]:
    """将IP从黑名单移除"""
    anti_fraud = get_anti_fraud_service(db)
    await anti_fraud.remove_ip_from_blacklist(ip_address)
    
    logger.info(
        "admin_ip_unblacklisted",
        ip=ip_address,
        operator=current_user.id
    )
    
    return ApiResponse[Dict[str, str]].success(
        data={"ip": ip_address},
        message="IP已从黑名单移除"
    )


@router.post("/users/{user_id}/ban", response_model=ApiResponse[Dict[str, Any]])
async def ban_user(
    user_id: int,
    reason: str = Query(..., description="封禁原因"),
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    current_user: User = Depends(get_current_admin_user)
) -> ApiResponse[Dict[str, Any]]:
    """
    封禁用户
    
    封禁后用户将无法登录
    """
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if user.is_banned:
        return ApiResponse[Dict[str, Any]].success(
            data={"user_id": user_id, "already_banned": True},
            message="用户已被封禁"
        )
    
    # 使用Repository封禁用户
    banned_user = await user_repo.ban_user(user_id, reason)
    
    logger.warning(
        "admin_user_banned",
        user_id=user_id,
        phone=user.phone,
        reason=reason,
        operator=current_user.id
    )
    
    return ApiResponse[Dict[str, Any]].success(
        data={
            "user_id": user_id,
            "phone": banned_user.phone if banned_user else user.phone,
            "ban_reason": reason,
            "banned_at": banned_user.banned_at.isoformat() if banned_user and banned_user.banned_at else None
        },
        message="用户已封禁"
    )


@router.post("/users/{user_id}/unban", response_model=ApiResponse[Dict[str, Any]])
async def unban_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    current_user: User = Depends(get_current_admin_user)
) -> ApiResponse[Dict[str, Any]]:
    """解封用户"""
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if not user.is_banned:
        return ApiResponse[Dict[str, Any]].success(
            data={"user_id": user_id, "already_active": True},
            message="用户未被封禁"
        )
    
    old_reason = user.ban_reason
    
    # 使用Repository解封用户
    unbanned_user = await user_repo.unban_user(user_id)
    
    logger.info(
        "admin_user_unbanned",
        user_id=user_id,
        phone=user.phone,
        previous_reason=old_reason,
        operator=current_user.id
    )
    
    return ApiResponse[Dict[str, Any]].success(
        data={
            "user_id": user_id, 
            "phone": unbanned_user.phone if unbanned_user else user.phone
        },
        message="用户已解封"
    )


@router.get("/recent-registrations", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_recent_registrations(
    hours: int = Query(24, ge=1, le=168, description="最近N小时"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
    current_user: User = Depends(get_current_admin_user)
) -> ApiResponse[List[Dict[str, Any]]]:
    """
    查看最近的注册记录
    
    用于审计和监控
    """
    # 使用Repository获取数据
    users = await user_repo.get_recent_registrations(hours=hours, limit=limit)
    
    registrations = [
        {
            "user_id": user.id,
            "phone": user.phone,
            "nickname": user.nickname,
            "registration_ip": user.registration_ip,
            "registration_source": user.registration_source,
            "registration_user_agent": user.registration_user_agent[:100] if user.registration_user_agent else None,
            "created_at": user.created_at.isoformat(),
            "is_banned": user.is_banned
        }
        for user in users
    ]
    
    return ApiResponse[List[Dict[str, Any]]].success(
        data=registrations,
        message=f"最近{hours}小时内有 {len(registrations)} 条注册记录"
    )
