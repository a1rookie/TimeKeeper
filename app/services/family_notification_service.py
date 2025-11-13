"""
Family Notification Service
家庭通知服务 - 处理家庭成员之间的通知
"""
import json
from typing import List, Optional
import structlog

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.family_notification import NotificationType
from app.repositories.family_notification_repository import FamilyNotificationRepository
from app.repositories.family_member_repository import FamilyMemberRepository

logger = structlog.get_logger(__name__)


class FamilyNotificationService:
    """家庭通知服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_repo = FamilyNotificationRepository(db)
        self.family_member_repo = FamilyMemberRepository(db)
    
    async def notify_reminder_completed(
        self,
        family_group_id: int,
        sender_id: int,
        reminder_id: int,
        completion_id: int,
        reminder_title: str,
        completed_status: str
    ):
        """
        通知家庭成员：提醒已完成
        
        Args:
            family_group_id: 家庭组ID
            sender_id: 完成提醒的用户ID
            reminder_id: 提醒ID
            completion_id: 完成记录ID
            reminder_title: 提醒标题
            completed_status: 完成状态（completed/delayed/skipped）
        """
        # 获取所有家庭成员
        members = await self.family_member_repo.get_group_members(family_group_id)
        receiver_ids = [m.user_id for m in members if m.user_id != sender_id]
        
        if not receiver_ids:
            logger.info(
                "no_family_members_to_notify",
                family_group_id=family_group_id,
                event="notification_skip"
            )
            return
        
        # 生成通知内容
        status_text = {
            "completed": "按时完成",
            "delayed": "延迟完成",
            "skipped": "跳过"
        }.get(completed_status, "完成")
        
        title = f"家庭提醒已{status_text}"
        content = f"「{reminder_title}」已被标记为{status_text}"
        
        metadata = {
            "reminder_id": reminder_id,
            "completion_id": completion_id,
            "status": completed_status
        }
        
        # 批量创建通知
        notifications = await self.notification_repo.batch_create_for_family_members(
            family_group_id=family_group_id,
            sender_id=sender_id,
            receiver_ids=receiver_ids,
            notification_type=NotificationType.REMINDER_COMPLETED,
            title=title,
            content=content,
            related_reminder_id=reminder_id,
            related_completion_id=completion_id,
            metadata_json=json.dumps(metadata)
        )
        
        logger.info(
            "family_reminder_completed_notified",
            family_group_id=family_group_id,
            sender_id=sender_id,
            reminder_id=reminder_id,
            notification_count=len(notifications),
            event="notification_sent"
        )
        
        return notifications
    
    async def notify_reminder_created(
        self,
        family_group_id: int,
        sender_id: int,
        reminder_id: int,
        reminder_title: str
    ):
        """通知家庭成员：新建提醒"""
        members = await self.family_member_repo.get_group_members(family_group_id)
        receiver_ids = [m.user_id for m in members if m.user_id != sender_id]
        
        if not receiver_ids:
            return
        
        title = "新的家庭提醒"
        content = f"「{reminder_title}」已被创建"
        
        notifications = await self.notification_repo.batch_create_for_family_members(
            family_group_id=family_group_id,
            sender_id=sender_id,
            receiver_ids=receiver_ids,
            notification_type=NotificationType.REMINDER_CREATED,
            title=title,
            content=content,
            related_reminder_id=reminder_id
        )
        
        logger.info(
            "family_reminder_created_notified",
            family_group_id=family_group_id,
            notification_count=len(notifications),
            event="notification_sent"
        )
        
        return notifications
    
    async def notify_reminder_updated(
        self,
        family_group_id: int,
        sender_id: int,
        reminder_id: int,
        reminder_title: str
    ):
        """通知家庭成员：提醒已更新"""
        members = await self.family_member_repo.get_group_members(family_group_id)
        receiver_ids = [m.user_id for m in members if m.user_id != sender_id]
        
        if not receiver_ids:
            return
        
        title = "家庭提醒已更新"
        content = f"「{reminder_title}」已被修改"
        
        notifications = await self.notification_repo.batch_create_for_family_members(
            family_group_id=family_group_id,
            sender_id=sender_id,
            receiver_ids=receiver_ids,
            notification_type=NotificationType.REMINDER_UPDATED,
            title=title,
            content=content,
            related_reminder_id=reminder_id
        )
        
        logger.info(
            "family_reminder_updated_notified",
            family_group_id=family_group_id,
            notification_count=len(notifications),
            event="notification_sent"
        )
        
        return notifications


def get_notification_service(db: AsyncSession) -> FamilyNotificationService:
    """获取通知服务实例"""
    return FamilyNotificationService(db)
