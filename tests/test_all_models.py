"""测试所有模型导入"""
import sys
sys.path.insert(0, r"d:\pygithub\TimeKeeper\TimeKeeper")

# 测试导入所有模型
from app.models import (
    User, Reminder, PushTask, ReminderCompletion,
    FamilyGroup, FamilyMember, ReminderTemplate,
    UserCustomTemplate, TemplateShare, TemplateUsageRecord,
    TemplateLike, VoiceInput, PushLog, UserBehavior, SystemConfig
)

models = [
    User, Reminder, PushTask, ReminderCompletion,
    FamilyGroup, FamilyMember, ReminderTemplate,
    UserCustomTemplate, TemplateShare, TemplateUsageRecord,
    TemplateLike, VoiceInput, PushLog, UserBehavior, SystemConfig
]

print("All models imported successfully!\n")
print("Database Structure Overview:\n")

priority_groups = {
    "Priority 1 - Core Tables (4)": [User, Reminder, ReminderCompletion, PushTask],
    "Priority 2 - Family Sharing (2)": [FamilyGroup, FamilyMember],
    "Priority 3 - Template System (2)": [ReminderTemplate, UserCustomTemplate],
    "Priority 4 - Sharing Ecosystem (3)": [TemplateShare, TemplateUsageRecord, TemplateLike],
    "Priority 5 - Auxiliary Functions (4)": [VoiceInput, PushLog, UserBehavior, SystemConfig]
}

for priority, model_list in priority_groups.items():
    print(f"\n{priority}")
    for model in model_list:
        table_name = model.__tablename__
        columns_count = len([c for c in model.__table__.columns])
        print(f"  - {model.__name__:25s} -> {table_name:30s} ({columns_count} fields)")

print(f"\n\nTotal: {len(models)} models created!")
print("\nKey Relationships:")
print("  User -> Reminder -> PushTask -> PushLog")
print("  User -> FamilyGroup -> FamilyMember")
print("  Reminder -> ReminderCompletion")
print("  ReminderTemplate -> UserCustomTemplate -> TemplateShare")
print("  TemplateShare -> TemplateUsageRecord")
print("  TemplateShare -> TemplateLike")
