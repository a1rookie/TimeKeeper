"""
PushTask Repository
推送任务数据访问层
"""

from typing import List, Tuple
from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update
from datetime import datetime
from app.models.push_task import PushTask, PushStatus


class PushTaskRepository:
    """推送任务数据仓库（Async + 兼容类方法调用）"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------
    # 实例方法（用于通过实例操作）
    # -----------------
    async def get_by_id(self, task_id: int, user_id: int | None = None) -> PushTask | None:
        stmt = select(PushTask).where(PushTask.id == task_id)
        if user_id is not None:
            stmt = stmt.where(PushTask.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        reminder_id: int,
        user_id: int,
        title: str,
        scheduled_time: datetime,
        content: str | None = None,
        channels: list[str] | None = None,
        priority: int = 1,
        max_retries: int = 3
    ) -> PushTask:
        new_task = PushTask(
            reminder_id=reminder_id,
            user_id=user_id,
            title=title,
            content=content,
            channels=channels or ["app"],
            scheduled_time=scheduled_time,
            status=PushStatus.PENDING,
            retry_count=0,
            max_retries=max_retries,
            priority=priority
        )

        self.db.add(new_task)
        await self.db.commit()
        await self.db.refresh(new_task)
        return new_task

    async def update(self, task: PushTask, **update_data) -> PushTask:
        for k, v in update_data.items():
            setattr(task, k, v)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def update_status(
        self,
        task: PushTask,
        status: PushStatus,
        error_message: str | None = None,
        push_response: dict | None = None
    ) -> PushTask:
        task.status = status
        if status == PushStatus.SENT:
            task.sent_time = datetime.now()
            task.executed_at = datetime.now()
        elif status == PushStatus.FAILED:
            task.retry_count = (task.retry_count or 0) + 1
            if error_message:
                task.error_message = error_message

        if push_response:
            task.push_response = push_response

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_pending_tasks(self, before_time: datetime) -> Sequence[PushTask]:
        stmt = select(PushTask).where(
            and_(
                PushTask.status == PushStatus.PENDING,
                PushTask.scheduled_time <= before_time
            )
        ).order_by(PushTask.priority.desc(), PushTask.scheduled_time)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_failed_tasks_for_retry(self, max_retries: int = 3) -> Sequence[PushTask]:
        stmt = select(PushTask).where(
            and_(
                PushTask.status == PushStatus.FAILED,
                PushTask.retry_count < max_retries
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def cancel(self, task: PushTask) -> None:
        task.status = PushStatus.CANCELLED
        await self.db.commit()
        await self.db.refresh(task)

    async def cancel_tasks_by_reminder(self, reminder_id: int) -> int:
        stmt = (
            update(PushTask)
            .where(and_(PushTask.reminder_id == reminder_id, PushTask.status == PushStatus.PENDING))
            .values(status=PushStatus.CANCELLED)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        # 在异步模式下，rowcount 可能不可用，返回0表示已执行
        return getattr(result, 'rowcount', 0)

    async def count_by_status(self, user_id: int, status: PushStatus) -> int:
        stmt = select(func.count()).select_from(PushTask).where(
            and_(PushTask.user_id == user_id, PushTask.status == status)
        )
        result = await self.db.execute(stmt)
        return int(result.scalar_one())

    # -----------------
    # 类方法（兼容现有代码风格：通过类直接调用并传入 db 参数）
    # -----------------
    @staticmethod
    async def get_by_id_static(db: AsyncSession, task_id: int, user_id: int | None = None) -> PushTask | None:
        repo = PushTaskRepository(db)
        return await repo.get_by_id(task_id=task_id, user_id=user_id)

    @staticmethod
    async def list_by_user(
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        status: PushStatus | None = None,
        reminder_id: int | None = None
    ) -> Tuple[List[PushTask], int]:
        stmt = select(PushTask).where(PushTask.user_id == user_id)
        if status is not None:
            stmt = stmt.where(PushTask.status == status)
        if reminder_id is not None:
            stmt = stmt.where(PushTask.reminder_id == reminder_id)

        total_stmt = select(func.count()).select_from(PushTask).where(PushTask.user_id == user_id)
        if status is not None:
            total_stmt = total_stmt.where(PushTask.status == status)
        if reminder_id is not None:
            total_stmt = total_stmt.where(PushTask.reminder_id == reminder_id)

        total_res = await db.execute(total_stmt)
        total = int(total_res.scalar_one())

        stmt = stmt.order_by(PushTask.scheduled_time.desc()).offset(skip).limit(limit)
        res = await db.execute(stmt)
        tasks = list(res.scalars().all())
        return tasks, total

    @staticmethod
    async def create_static(db: AsyncSession, **kwargs) -> PushTask:
        repo = PushTaskRepository(db)
        return await repo.create(**kwargs)

    @staticmethod
    async def update_static(db: AsyncSession, task: PushTask, **update_data) -> PushTask:
        repo = PushTaskRepository(db)
        return await repo.update(task=task, **update_data)

    @staticmethod
    async def update_status_static(db: AsyncSession, task: PushTask, status: PushStatus, error_message: str | None = None, push_response: dict | None = None) -> PushTask:
        repo = PushTaskRepository(db)
        return await repo.update_status(task=task, status=status, error_message=error_message, push_response=push_response)

    @staticmethod
    async def get_pending_tasks_static(db: AsyncSession, before_time: datetime) -> Sequence[PushTask]:
        repo = PushTaskRepository(db)
        return await repo.get_pending_tasks(before_time=before_time)

    @staticmethod
    async def cancel_static(db: AsyncSession, task: PushTask) -> None:
        repo = PushTaskRepository(db)
        return await repo.cancel(task=task)

    @staticmethod
    async def reset_for_retry(db: AsyncSession, task: PushTask) -> PushTask:
        # 将任务重置为PENDING并清零重试计数
        task.status = PushStatus.PENDING
        task.retry_count = 0
        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def get_statistics(db: AsyncSession, user_id: int) -> dict:
        # 返回简单统计数据：各状态计数
        stats = {}
        for status in [PushStatus.PENDING, PushStatus.SENT, PushStatus.FAILED, PushStatus.CANCELLED]:
            stmt = select(func.count()).select_from(PushTask).where(
                and_(PushTask.user_id == user_id, PushTask.status == status)
            )
            res = await db.execute(stmt)
            stats[status.name.lower()] = int(res.scalar_one())
        return stats
