"""
简化版系统模板初始化
"""
from app.core.database import SessionLocal
from app.models.reminder_template import ReminderTemplate

def init_templates():
    db = SessionLocal()
    try:
        templates = [
            {"name": "每日吃药", "category": "health", "description_template": "每天按时服药", "default_recurrence_type": "daily", "default_recurrence_config": {"time": "08:00"}, "default_advance_days": 0},
            {"name": "每月房租", "category": "life", "description_template": "每月缴纳房租", "default_recurrence_type": "monthly", "default_recurrence_config": {"day": 1}, "default_advance_days": 3},
            {"name": "信用卡还款", "category": "life", "description_template": "信用卡还款", "default_recurrence_type": "monthly", "default_recurrence_config": {"day": 20}, "default_advance_days": 3},
            {"name": "周例会", "category": "work", "description_template": "每周团队例会", "default_recurrence_type": "weekly", "default_recurrence_config": {"weekdays": [1], "time": "10:00"}, "default_advance_days": 0},
            {"name": "生日提醒", "category": "social", "description_template": "生日提醒", "default_recurrence_type": "yearly", "default_recurrence_config": {"month": 1, "day": 1}, "default_advance_days": 3},
            {"name": "宠物疫苗", "category": "pet", "description_template": "宠物疫苗接种", "default_recurrence_type": "yearly", "default_recurrence_config": {"month": 3, "day": 1}, "default_advance_days": 7},
            {"name": "车辆保养", "category": "vehicle", "description_template": "定期车辆保养", "default_recurrence_type": "custom", "default_recurrence_config": {"months": 6}, "default_advance_days": 7},
        ]
        
        created = 0
        for t in templates:
            existing = db.query(ReminderTemplate).filter_by(name=t["name"]).first()
            if not existing:
                db.add(ReminderTemplate(**t))
                created += 1
                print(f"✓ {t['name']}")
        
        db.commit()
        print(f"\n✅ 创建了 {created} 个模板")
    except Exception as e:
        print(f"❌ 错误: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_templates()
