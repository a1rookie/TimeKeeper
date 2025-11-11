"""
Push Task Repository - SQLAlchemy 2.0
推送任务数据访问层
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.models.push_task import PushTask, PushStatus


class PushTaskRepository:
    """推送任务仓储类 - 使用SQLAlchemy 2.0语法"""
    
    @staticmethod
    def create(
        db: Session,
        user_id: int,
        reminder_id: int,
        title: str,
        content: str,
        channels: List[str],
        scheduled_time: datetime
    ) -> PushTask:
        """
        创建推送任务
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            reminder_id: 提醒ID
            title: 推送标题
            content: 推送内容
            channels: 推送渠道列表
            scheduled_time: 计划推送时间
            
        Returns:
            创建的推送任务
        """
        push_task = PushTask(
            user_id=user_id,
            reminder_id=reminder_id,
            title=title,
            content=content,
            channels=channels,
            scheduled_time=scheduled_time,
            status=PushStatus.PENDING
        )
        
        db.add(push_task)
        db.commit()
        db.refresh(push_task)
        
        return push_task
    
    @staticmethod
    def get_by_id(db: Session, task_id: int, user_id: int) -> Optional[PushTask]:
        """
        根据ID获取推送任务（带用户权限检查）
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            推送任务或None
        """
        stmt = select(PushTask).where(
            and_(
                PushTask.id == task_id,
                PushTask.user_id == user_id
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    def get_by_id_without_user_check(db: Session, task_id: int) -> Optional[PushTask]:
        """
        根据ID获取推送任务（不检查用户权限，用于调度器）
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            
        Returns:
            推送任务或None
        """
        stmt = select(PushTask).where(PushTask.id == task_id)
        result = db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    def list_by_user(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        status: Optional[PushStatus] = None,
        reminder_id: Optional[int] = None
    ) -> tuple[List[PushTask], int]:
        """
        获取用户的推送任务列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过记录数
            limit: 返回记录数
            status: 状态筛选（可选）
            reminder_id: 提醒ID筛选（可选）
            
        Returns:
            (任务列表, 总数)
        """
        # 构建基础查询条件
        conditions = [PushTask.user_id == user_id]
        
        if status is not None:
            conditions.append(PushTask.status == status)
        
        if reminder_id is not None:
            conditions.append(PushTask.reminder_id == reminder_id)
        
        # 查询总数
        count_stmt = select(func.count()).select_from(PushTask).where(and_(*conditions))
        total = db.execute(count_stmt).scalar_one()
        
        # 查询列表
        stmt = (
            select(PushTask)
            .where(and_(*conditions))
            .order_by(PushTask.scheduled_time.desc())
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(stmt)
        tasks = result.scalars().all()
        
        return tasks, total
    
    @staticmethod
    def get_pending_tasks(db: Session, before_time: datetime) -> List[PushTask]:
        """
        获取待推送的任务（scheduled_time <= before_time 且状态为 PENDING）
        
        Args:
            db: 数据库会话
            before_time: 截止时间
            
        Returns:
            待推送任务列表
        """
        stmt = (
            select(PushTask)
            .where(
                and_(
                    PushTask.status == PushStatus.PENDING,
                    PushTask.scheduled_time <= before_time
                )
            )
            .order_by(PushTask.scheduled_time.asc())
        )
        result = db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    def update(
        db: Session,
        task: PushTask,
        **kwargs
    ) -> PushTask:
        """
        更新推送任务
        
        Args:
            db: 数据库会话
            task: 推送任务对象
            **kwargs: 要更新的字段
            
        Returns:
            更新后的任务
        """
        for key, value in kwargs.items():
            if hasattr(task, key) and value is not None:
                setattr(task, key, value)
        
        db.commit()
        db.refresh(task)
        
        return task
    
    @staticmethod
    def cancel(db: Session, task: PushTask) -> PushTask:
        """
        取消推送任务
        
        Args:
            db: 数据库会话
            task: 推送任务对象
            
        Returns:
            取消后的任务
        """
        task.status = PushStatus.CANCELLED
        db.commit()
        db.refresh(task)
        
        return task
    
    @staticmethod
    def mark_as_sent(
        db: Session,
        task: PushTask,
        push_response: Optional[dict] = None
    ) -> PushTask:
        """
        标记任务为已发送
        
        Args:
            db: 数据库会话
            task: 推送任务对象
            push_response: 推送响应数据（可选）
            
        Returns:
            更新后的任务
        """
        task.status = PushStatus.SENT
        task.sent_time = datetime.now()
        task.push_response = push_response
        
        db.commit()
        db.refresh(task)
        
        return task
    
    @staticmethod
    def mark_as_failed(
        db: Session,
        task: PushTask,
        error_message: str
    ) -> PushTask:
        """
        标记任务为失败
        
        Args:
            db: 数据库会话
            task: 推送任务对象
            error_message: 错误信息
            
        Returns:
            更新后的任务
        """
        task.status = PushStatus.FAILED
        task.error_message = error_message
        task.retry_count += 1
        
        db.commit()
        db.refresh(task)
        
        return task
    
    @staticmethod
    def reset_for_retry(db: Session, task: PushTask) -> PushTask:
        """
        重置任务状态以便重试
        
        Args:
            db: 数据库会话
            task: 推送任务对象
            
        Returns:
            重置后的任务
        """
        task.status = PushStatus.PENDING
        task.scheduled_time = datetime.now()
        task.retry_count = 0
        task.error_message = None
        
        db.commit()
        db.refresh(task)
        
        return task
    
    @staticmethod
    def get_statistics(db: Session, user_id: int) -> dict:
        """
        获取用户的推送统计信息
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            统计信息字典
        """
        # 总数
        total_stmt = (
            select(func.count())
            .select_from(PushTask)
            .where(PushTask.user_id == user_id)
        )
        total = db.execute(total_stmt).scalar_one()
        
        # 各状态数量
        stats = {}
        for status in [PushStatus.PENDING, PushStatus.SENT, PushStatus.FAILED, PushStatus.CANCELLED]:
            stmt = (
                select(func.count())
                .select_from(PushTask)
                .where(
                    and_(
                        PushTask.user_id == user_id,
                        PushTask.status == status
                    )
                )
            )
            count = db.execute(stmt).scalar_one()
            stats[status.value] = count
        
        # 成功率
        success_rate = round(stats['sent'] / total * 100, 2) if total > 0 else 0
        
        return {
            "total": total,
            "pending": stats['pending'],
            "sent": stats['sent'],
            "failed": stats['failed'],
            "cancelled": stats['cancelled'],
            "success_rate": success_rate
        }
