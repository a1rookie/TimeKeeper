"""
Health Check & System Monitoring Endpoints
用于生产环境监控和问题排查
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.redis import get_redis
from app.core.config import settings
from app.schemas.response import ApiResponse

router = APIRouter()


@router.get("/health", response_model=ApiResponse[Dict[str, Any]])
async def health_check() -> ApiResponse[Dict[str, Any]]:
    """
    健康检查 - 不依赖任何服务
    用于负载均衡器/k8s存活探针
    """
    return ApiResponse[Dict[str, Any]].success(data={
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    })


@router.get("/readiness", response_model=ApiResponse[Dict[str, Any]])
async def readiness_check(db: AsyncSession = Depends(get_db)) -> ApiResponse[Dict[str, Any]]:
    """
    就绪检查 - 检查所有依赖服务
    用于k8s就绪探针，确保服务可接受流量
    """
    checks = {
        "database": "unknown",
        "redis": "unknown"
    }
    
    # 检查数据库
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
    
    # 检查Redis
    try:
        redis_client = get_redis()
        if redis_client and redis_client.ping():
            checks["redis"] = "connected"
        else:
            checks["redis"] = "unavailable"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"
    
    # 判断整体状态
    all_healthy = all(
        status in ["connected", "unavailable"] 
        for status in checks.values()
    )
    
    return ApiResponse[Dict[str, Any]].success(data={
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks
    })
