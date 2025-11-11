"""
Push Task API Endpoints
推送任务相关API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.push_task import PushTask, PushStatus
from app.schemas.push_task import (
    PushTaskCreate,
    PushTaskResponse,
    PushTaskUpdate,
    PushTaskList
)
from app.services.push_scheduler import create_push_task_for_reminder

router = APIRouter(prefix="/push-tasks", tags=["push-tasks"])


@router.get("/", response_model=PushTaskList)
async def list_push_tasks(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
    status: Optional[PushStatus] = Query(None, description="按状态筛选"),
    reminder_id: Optional[int] = Query(None, description="按提醒ID筛选"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取推送任务列表
    """
    query = db.query(PushTask).filter(PushTask.user_id == current_user.id)
    
    # 状态筛选
    if status:
        query = query.filter(PushTask.status == status)
    
    # 提醒ID筛选
    if reminder_id:
        query = query.filter(PushTask.reminder_id == reminder_id)
    
    # 总数
    total = query.count()
    
    # 分页
    tasks = query.order_by(PushTask.scheduled_time.desc()).offset(skip).limit(limit).all()
    
    return {
        "tasks": tasks,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{task_id}", response_model=PushTaskResponse)
async def get_push_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取单个推送任务详情
    """
    task = db.query(PushTask).filter(
        PushTask.id == task_id,
        PushTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Push task not found"
        )
    
    return task


@router.post("/", response_model=PushTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_push_task(
    task_data: PushTaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    创建推送任务
    """
    try:
        task = create_push_task_for_reminder(
            db=db,
            reminder_id=task_data.reminder_id,
            user_id=current_user.id,
            scheduled_time=task_data.scheduled_time
        )
        return task
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create push task: {str(e)}"
        )


@router.put("/{task_id}", response_model=PushTaskResponse)
async def update_push_task(
    task_id: int,
    task_data: PushTaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    更新推送任务
    """
    task = db.query(PushTask).filter(
        PushTask.id == task_id,
        PushTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Push task not found"
        )
    
    # 只允许更新PENDING状态的任务
    if task.status != PushStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only update pending tasks"
        )
    
    # 更新字段
    if task_data.scheduled_time is not None:
        task.scheduled_time = task_data.scheduled_time
    
    if task_data.title is not None:
        task.title = task_data.title
    
    if task_data.content is not None:
        task.content = task_data.content
    
    db.commit()
    db.refresh(task)
    
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_push_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    取消推送任务（将状态设为CANCELLED）
    """
    task = db.query(PushTask).filter(
        PushTask.id == task_id,
        PushTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Push task not found"
        )
    
    # 只允许取消PENDING状态的任务
    if task.status != PushStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel pending tasks"
        )
    
    task.status = PushStatus.CANCELLED
    db.commit()


@router.post("/{task_id}/retry", response_model=PushTaskResponse)
async def retry_push_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    重试失败的推送任务
    """
    task = db.query(PushTask).filter(
        PushTask.id == task_id,
        PushTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Push task not found"
        )
    
    # 只允许重试FAILED状态的任务
    if task.status != PushStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only retry failed tasks"
        )
    
    # 重置状态
    task.status = PushStatus.PENDING
    task.scheduled_time = datetime.now()
    task.retry_count = 0
    task.error_message = None
    
    db.commit()
    db.refresh(task)
    
    return task


@router.get("/stats/summary")
async def get_push_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取推送统计信息
    """
    user_tasks = db.query(PushTask).filter(PushTask.user_id == current_user.id)
    
    total = user_tasks.count()
    pending = user_tasks.filter(PushTask.status == PushStatus.PENDING).count()
    sent = user_tasks.filter(PushTask.status == PushStatus.SENT).count()
    failed = user_tasks.filter(PushTask.status == PushStatus.FAILED).count()
    cancelled = user_tasks.filter(PushTask.status == PushStatus.CANCELLED).count()
    
    return {
        "total": total,
        "pending": pending,
        "sent": sent,
        "failed": failed,
        "cancelled": cancelled,
        "success_rate": round(sent / total * 100, 2) if total > 0 else 0
    }
