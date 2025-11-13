"""
Monitoring and Health Check API
运维监控和健康检查 API
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
import structlog
import time
from datetime import datetime, timedelta

from app.core.database import get_db
from app.schemas.response import ApiResponse
from app.models.user import User
from app.models.reminder import Reminder
from app.models.reminder_completion import ReminderCompletion, CompletionStatus
from app.models.family_group import FamilyGroup
from app.models.template_share import TemplateShare

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health", response_model=ApiResponse[Dict[str, Any]])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    健康检查端点
    
    检查项:
    - 数据库连接
    - 基础查询性能
    - 系统时间
    """
    start_time = time.time()
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # 1. 数据库连接检查
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        health_status["checks"]["database"] = {
            "status": "ok",
            "message": "数据库连接正常"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "error",
            "message": f"数据库连接失败: {str(e)}"
        }
        logger.error("health_check_database_error", error=str(e), event="health_check_fail")
    
    # 2. 数据库查询性能检查
    try:
        query_start = time.time()
        result = await db.execute(select(func.count()).select_from(User))
        user_count = result.scalar()
        query_time = (time.time() - query_start) * 1000  # 转换为毫秒
        
        health_status["checks"]["database_query"] = {
            "status": "ok" if query_time < 100 else "warning",
            "query_time_ms": round(query_time, 2),
            "message": f"查询耗时 {round(query_time, 2)}ms"
        }
    except Exception as e:
        health_status["checks"]["database_query"] = {
            "status": "error",
            "message": f"查询失败: {str(e)}"
        }
    
    # 3. 响应时间
    response_time = (time.time() - start_time) * 1000
    health_status["response_time_ms"] = round(response_time, 2)
    
    logger.info(
        "health_check",
        status=health_status["status"],
        response_time_ms=health_status["response_time_ms"],
        event="health_check_complete"
    )
    
    return ApiResponse.success(data=health_status)


@router.get("/metrics", response_model=ApiResponse[Dict[str, Any]])
async def get_system_metrics(db: AsyncSession = Depends(get_db)):
    """
    系统指标统计
    
    包括:
    - 用户统计
    - 提醒统计
    - 完成率统计
    - 家庭组统计
    - 模板统计
    """
    metrics = {}
    
    try:
        # 1. 用户统计
        result = await db.execute(select(func.count()).select_from(User))
        total_users = result.scalar() or 0
        
        # 活跃用户（最近30天有登录）
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        result = await db.execute(
            select(func.count()).select_from(User).where(User.updated_at >= thirty_days_ago)
        )
        active_users = result.scalar() or 0
        
        metrics["users"] = {
            "total": total_users,
            "active_30d": active_users,
            "active_rate": round(active_users / total_users * 100, 2) if total_users > 0 else 0
        }
        
        # 2. 提醒统计
        result = await db.execute(select(func.count()).select_from(Reminder))
        total_reminders = result.scalar() or 0
        
        result = await db.execute(
            select(func.count()).select_from(Reminder).where(Reminder.is_active == True)
        )
        active_reminders = result.scalar() or 0
        
        metrics["reminders"] = {
            "total": total_reminders,
            "active": active_reminders,
            "inactive": total_reminders - active_reminders
        }
        
        # 3. 完成率统计（最近7天）
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        result = await db.execute(
            select(func.count()).select_from(ReminderCompletion).where(
                ReminderCompletion.scheduled_time >= seven_days_ago
            )
        )
        total_completions = result.scalar() or 0
        
        result = await db.execute(
            select(func.count()).select_from(ReminderCompletion).where(
                ReminderCompletion.scheduled_time >= seven_days_ago,
                ReminderCompletion.status == CompletionStatus.COMPLETED
            )
        )
        completed_count = result.scalar() or 0
        
        result = await db.execute(
            select(func.count()).select_from(ReminderCompletion).where(
                ReminderCompletion.scheduled_time >= seven_days_ago,
                ReminderCompletion.status == CompletionStatus.DELAYED
            )
        )
        delayed_count = result.scalar() or 0
        
        metrics["completions_7d"] = {
            "total": total_completions,
            "completed": completed_count,
            "delayed": delayed_count,
            "completion_rate": round((completed_count + delayed_count) / total_completions * 100, 2) if total_completions > 0 else 0
        }
        
        # 4. 家庭组统计
        result = await db.execute(select(func.count()).select_from(FamilyGroup))
        total_families = result.scalar() or 0
        
        result = await db.execute(
            select(func.count()).select_from(FamilyGroup).where(FamilyGroup.is_active == True)
        )
        active_families = result.scalar() or 0
        
        metrics["families"] = {
            "total": total_families,
            "active": active_families
        }
        
        # 5. 模板市场统计
        result = await db.execute(
            select(func.count()).select_from(TemplateShare).where(TemplateShare.is_active == True)
        )
        active_shares = result.scalar() or 0
        
        result = await db.execute(
            select(func.sum(TemplateShare.usage_count)).select_from(TemplateShare)
        )
        total_template_uses = result.scalar() or 0
        
        metrics["template_market"] = {
            "active_shares": active_shares,
            "total_uses": total_template_uses
        }
        
        logger.info(
            "metrics_retrieved",
            total_users=total_users,
            total_reminders=total_reminders,
            event="metrics_collected"
        )
        
        return ApiResponse.success(data=metrics)
        
    except Exception as e:
        logger.error("metrics_error", error=str(e), event="metrics_collection_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统指标失败: {str(e)}"
        )


@router.get("/metrics/performance", response_model=ApiResponse[Dict[str, Any]])
async def get_performance_metrics(db: AsyncSession = Depends(get_db)):
    """
    性能指标
    
    包括:
    - 数据库查询性能
    - 各表记录数
    - 数据库大小估算
    """
    performance = {}
    
    try:
        # 1. 各表查询性能测试
        tables = [
            ("users", User),
            ("reminders", Reminder),
            ("reminder_completions", ReminderCompletion),
            ("family_groups", FamilyGroup),
            ("template_shares", TemplateShare)
        ]
        
        table_stats = {}
        for table_name, model in tables:
            start_time = time.time()
            result = await db.execute(select(func.count()).select_from(model))
            count = result.scalar() or 0
            query_time = (time.time() - start_time) * 1000
            
            table_stats[table_name] = {
                "record_count": count,
                "query_time_ms": round(query_time, 2),
                "status": "ok" if query_time < 50 else "warning" if query_time < 100 else "slow"
            }
        
        performance["table_stats"] = table_stats
        
        # 2. 平均查询时间
        avg_query_time = sum(s["query_time_ms"] for s in table_stats.values()) / len(table_stats)
        performance["avg_query_time_ms"] = round(avg_query_time, 2)
        performance["performance_grade"] = "excellent" if avg_query_time < 20 else "good" if avg_query_time < 50 else "acceptable" if avg_query_time < 100 else "poor"
        
        logger.info(
            "performance_metrics",
            avg_query_time_ms=performance["avg_query_time_ms"],
            grade=performance["performance_grade"],
            event="performance_measured"
        )
        
        return ApiResponse.success(data=performance)
        
    except Exception as e:
        logger.error("performance_metrics_error", error=str(e), event="performance_measurement_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取性能指标失败: {str(e)}"
        )


@router.get("/metrics/growth", response_model=ApiResponse[Dict[str, Any]])
async def get_growth_metrics(db: AsyncSession = Depends(get_db)):
    """
    增长指标
    
    包括:
    - 每日新增用户
    - 每日新增提醒
    - 每日完成率趋势
    """
    growth = {}
    
    try:
        # 最近7天的增长数据
        days = []
        for i in range(7):
            day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            # 新增用户
            result = await db.execute(
                select(func.count()).select_from(User).where(
                    User.created_at >= day_start,
                    User.created_at < day_end
                )
            )
            new_users = result.scalar() or 0
            
            # 新增提醒
            result = await db.execute(
                select(func.count()).select_from(Reminder).where(
                    Reminder.created_at >= day_start,
                    Reminder.created_at < day_end
                )
            )
            new_reminders = result.scalar() or 0
            
            # 当天完成率
            result = await db.execute(
                select(func.count()).select_from(ReminderCompletion).where(
                    ReminderCompletion.scheduled_time >= day_start,
                    ReminderCompletion.scheduled_time < day_end
                )
            )
            total_scheduled = result.scalar() or 0
            
            result = await db.execute(
                select(func.count()).select_from(ReminderCompletion).where(
                    ReminderCompletion.scheduled_time >= day_start,
                    ReminderCompletion.scheduled_time < day_end,
                    ReminderCompletion.status.in_([CompletionStatus.COMPLETED, CompletionStatus.DELAYED])
                )
            )
            completed = result.scalar() or 0
            
            days.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "new_users": new_users,
                "new_reminders": new_reminders,
                "completion_rate": round(completed / total_scheduled * 100, 2) if total_scheduled > 0 else 0
            })
        
        growth["daily_stats"] = list(reversed(days))
        
        logger.info(
            "growth_metrics",
            days_analyzed=len(days),
            event="growth_analyzed"
        )
        
        return ApiResponse.success(data=growth)
        
    except Exception as e:
        logger.error("growth_metrics_error", error=str(e), event="growth_analysis_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取增长指标失败: {str(e)}"
        )
