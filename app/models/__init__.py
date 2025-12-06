"""Database models"""

# Core models
from app.models.user import User
from app.models.reminder import Reminder
from app.models.push_task import PushTask
from app.models.reminder_completion import ReminderCompletion

# Family models
from app.models.family_group import FamilyGroup
from app.models.family_member import FamilyMember
from app.models.family_notification import FamilyNotification

# Template models
from app.models.reminder_template import ReminderTemplate
from app.models.user_custom_template import UserCustomTemplate
from app.models.template_share import TemplateShare
from app.models.template_usage_record import TemplateUsageRecord
from app.models.template_like import TemplateLike

# Notification models
from app.models.reminder_notification import ReminderNotification

# Auxiliary models
from app.models.voice_input import VoiceInput
from app.models.push_log import PushLog
from app.models.sms_log import SmsLog
from app.models.user_behavior import UserBehavior
from app.models.system_config import SystemConfig

__all__ = [
    # Core
    "User",
    "Reminder",
    "PushTask",
    "ReminderCompletion",
    # Family
    "FamilyGroup",
    "FamilyMember",
    "FamilyNotification",
    # Template
    "ReminderTemplate",
    "UserCustomTemplate",
    "TemplateShare",
    "TemplateUsageRecord",
    "TemplateLike",
    # Notification
    "ReminderNotification",
    # Auxiliary
    "VoiceInput",
    "PushLog",
    "SmsLog",
    "UserBehavior",
    "SystemConfig",
]
