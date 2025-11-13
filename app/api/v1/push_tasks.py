"""
Push Task API Endpoints
推送任务相关API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.push_task import PushStatus
from app.schemas.response import ApiResponse
from app.schemas.push_task import (
    PushTaskCreate,
    PushTaskResponse,
    PushTaskUpdate,
    PushTaskList
)
from app.repositories.push_task_repository import PushTaskRepository
from app.services.push_scheduler import create_push_task_for_reminder

router = APIRouter(prefix="/push-tasks", tags=["push-tasks"])


@router.get("/", response_model=ApiResponse[PushTaskList])
async def list_push_tasks(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
    status: Optional[PushStatus] = Query(None, description="按状态筛选"),
    reminder_id: Optional[int] = Query(None, description="按提醒ID筛选"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取推送任务列表
    """
    tasks, total = PushTaskRepository.list_by_user(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status=status,
        reminder_id=reminder_id
    )
    
    return ApiResponse.success(data={
        "tasks": tasks,
        "total": total,
        "skip": skip,
        "limit": limit
    })


@router.get("/{task_id}", response_model=ApiResponse[PushTaskResponse])
async def get_push_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取单个推送任务详情
    """
    task = PushTaskRepository.get_by_id(
        db=db,
        task_id=task_id,
        user_id=current_user.id
    )
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Push task not found"
        )
    
    return ApiResponse.success(data=task)


@router.post("/", response_model=ApiResponse[PushTaskResponse], status_code=status.HTTP_201_CREATED)
async def create_push_task(
    task_data: PushTaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
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
        return ApiResponse.success(data=task)
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


@router.put("/{task_id}", response_model=ApiResponse[PushTaskResponse])
async def update_push_task(
    task_id: int,
    task_data: PushTaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新推送任务
    """
    task = PushTaskRepository.get_by_id(
        db=db,
        task_id=task_id,
        user_id=current_user.id
    )
    
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
    update_data = {}
    if task_data.scheduled_time is not None:
        update_data["scheduled_time"] = task_data.scheduled_time
    if task_data.title is not None:
        update_data["title"] = task_data.title
    if task_data.content is not None:
        update_data["content"] = task_data.content
    
    task = PushTaskRepository.update(db=db, task=task, **update_data)
    
    return ApiResponse.success(data=task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_push_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    取消推送任务（将状态设为CANCELLED）
    """
    task = PushTaskRepository.get_by_id(
        db=db,
        task_id=task_id,
        user_id=current_user.id
    )
    
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
    
    PushTaskRepository.cancel(db=db, task=task)


@router.post("/{task_id}/retry", response_model=ApiResponse[PushTaskResponse])
async def retry_push_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    重试失败的推送任务
    """
    task = PushTaskRepository.get_by_id(
        db=db,
        task_id=task_id,
        user_id=current_user.id
    )
    
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
    
    # 重置状态以便重试
    task = PushTaskRepository.reset_for_retry(db=db, task=task)
    
    return ApiResponse.success(data=task)


@router.get("/stats/summary", response_model=ApiResponse[dict])
async def get_push_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取推送统计信息
    """
    return ApiResponse.success(data=PushTaskRepository.get_statistics(db=db, user_id=current_user.id))
