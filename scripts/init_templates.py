"""
初始化系统模板数据
为常见场景创建预置模板
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.reminder_template import ReminderTemplate


def init_system_templates():
    """初始化系统模板"""
    db: Session = SessionLocal()
    try:
        templates = [
            # ==================== 健康类 ====================
            {"name": "每日吃药提醒", "category": "health", "description_template": "适合需要每天按时服药的场景", "default_recurrence_type": "daily", "default_recurrence_config": {"time": "08:00"}, "default_advance_days": 0},
            {"name": "定期体检", "category": "health", "description_template": "每年一次健康体检提醒",
                "default_recurrence_type": "yearly",
                "default_recurrence_config": {"month": 6, "day": 1},
                "default_remind_advance_days": 7
            },
            {
                "name": "疫苗接种",
                "category": "health",
                "description": "疫苗接种提醒（可自定义间隔）",
                "default_recurrence_type": "custom",
                "default_recurrence_config": {"months": 6},
                "default_remind_advance_days": 3
            },
            {
                "name": "每周运动打卡",
                "category": "health",
                "description": "每周固定时间运动提醒",
                "default_recurrence_type": "weekly",
                "default_recurrence_config": {"weekdays": [1, 3, 5], "time": "18:00"},
                "default_remind_advance_days": 0
            },
            
            # ==================== 生活类 ====================
            {
                "name": "每月房租",
                "category": "life",
                "description": "每月固定日期缴纳房租",
                "default_recurrence_type": "monthly",
                "default_recurrence_config": {"day": 1},
                "default_remind_advance_days": 3
            },
            {
                "name": "水电费缴纳",
                "category": "life",
                "description": "每月水电费缴纳提醒",
                "default_recurrence_type": "monthly",
                "default_recurrence_config": {"day": 25},
                "default_remind_advance_days": 2
            },
            {
                "name": "垃圾分类提醒",
                "category": "life",
                "description": "每周垃圾日提醒",
                "default_recurrence_type": "weekly",
                "default_recurrence_config": {"weekdays": [2, 5], "time": "19:00"},
                "default_remind_advance_days": 0
            },
            {
                "name": "信用卡还款",
                "category": "life",
                "description": "每月信用卡还款日提醒",
                "default_recurrence_type": "monthly",
                "default_recurrence_config": {"day": 20},
                "default_remind_advance_days": 3
            },
            
            # ==================== 工作类 ====================
            {
                "name": "周例会",
                "category": "work",
                "description": "每周固定时间的团队例会",
                "default_recurrence_type": "weekly",
                "default_recurrence_config": {"weekdays": [1], "time": "10:00"},
                "default_remind_advance_days": 0
            },
            {
                "name": "月度总结",
                "category": "work",
                "description": "每月最后一天提交月度总结",
                "default_recurrence_type": "monthly",
                "default_recurrence_config": {"day": -1},
                "default_remind_advance_days": 2
            },
            {
                "name": "项目汇报",
                "category": "work",
                "description": "每两周一次的项目进度汇报",
                "default_recurrence_type": "custom",
                "default_recurrence_config": {"weeks": 2, "weekday": 5, "time": "15:00"},
                "default_remind_advance_days": 1
            },
            
            # ==================== 学习类 ====================
            {
                "name": "每日单词打卡",
                "category": "study",
                "description": "每天背单词提醒",
                "default_recurrence_type": "daily",
                "default_recurrence_config": {"time": "21:00"},
                "default_remind_advance_days": 0
            },
            {
                "name": "考试倒计时",
                "category": "study",
                "description": "重要考试前的复习提醒",
                "default_recurrence_type": "once",
                "default_recurrence_config": {},
                "default_remind_advance_days": 7
            },
            {
                "name": "读书计划",
                "category": "study",
                "description": "每周阅读打卡",
                "default_recurrence_type": "weekly",
                "default_recurrence_config": {"weekdays": [0, 6], "time": "20:00"},
                "default_remind_advance_days": 0
            },
            
            # ==================== 社交类 ====================
            {
                "name": "家人生日",
                "category": "social",
                "description": "家人生日提醒",
                "default_recurrence_type": "yearly",
                "default_recurrence_config": {"month": 1, "day": 1},
                "default_remind_advance_days": 3
            },
            {
                "name": "节日祝福",
                "category": "social",
                "description": "重要节日发送祝福提醒",
                "default_recurrence_type": "yearly",
                "default_recurrence_config": {"month": 1, "day": 1},
                "default_remind_advance_days": 1
            },
            {
                "name": "聚会约定",
                "category": "social",
                "description": "定期朋友聚会提醒",
                "default_recurrence_type": "custom",
                "default_recurrence_config": {"months": 3},
                "default_remind_advance_days": 7
            },
            
            # ==================== 宠物护理类 ====================
            {
                "name": "宠物喂食",
                "category": "pet",
                "description": "每天固定时间喂食提醒",
                "default_recurrence_type": "daily",
                "default_recurrence_config": {"time": "07:00"},
                "default_remind_advance_days": 0
            },
            {
                "name": "宠物疫苗",
                "category": "pet",
                "description": "宠物疫苗接种提醒",
                "default_recurrence_type": "yearly",
                "default_recurrence_config": {"month": 3, "day": 1},
                "default_remind_advance_days": 7
            },
            {
                "name": "宠物驱虫",
                "category": "pet",
                "description": "每月宠物驱虫提醒",
                "default_recurrence_type": "monthly",
                "default_recurrence_config": {"day": 1},
                "default_remind_advance_days": 1
            },
            {
                "name": "宠物洗澡",
                "category": "pet",
                "description": "每两周宠物洗澡提醒",
                "default_recurrence_type": "custom",
                "default_recurrence_config": {"weeks": 2, "weekday": 6, "time": "10:00"},
                "default_remind_advance_days": 0
            },
            
            # ==================== 车辆维护类 ====================
            {
                "name": "车辆保养",
                "category": "vehicle",
                "description": "定期车辆保养提醒",
                "default_recurrence_type": "custom",
                "default_recurrence_config": {"months": 6},
                "default_remind_advance_days": 7
            },
            {
                "name": "保险续费",
                "category": "vehicle",
                "description": "车辆保险到期提醒",
                "default_recurrence_type": "yearly",
                "default_recurrence_config": {"month": 1, "day": 1},
                "default_remind_advance_days": 30
            },
            {
                "name": "年检提醒",
                "category": "vehicle",
                "description": "车辆年检提醒",
                "default_recurrence_type": "yearly",
                "default_recurrence_config": {"month": 12, "day": 1},
                "default_remind_advance_days": 30
            },
            
            # ==================== 其他类 ====================
            {
                "name": "会员续费",
                "category": "other",
                "description": "各类会员到期续费提醒",
                "default_recurrence_type": "monthly",
                "default_recurrence_config": {"day": 1},
                "default_remind_advance_days": 3
            },
            {
                "name": "定期理发",
                "category": "other",
                "description": "每月理发提醒",
                "default_recurrence_type": "custom",
                "default_recurrence_config": {"weeks": 4},
                "default_remind_advance_days": 0
            },
            {
                "name": "植物浇水",
                "category": "other",
                "description": "家中植物定期浇水",
                "default_recurrence_type": "custom",
                "default_recurrence_config": {"days": 3},
                "default_remind_advance_days": 0
            },
        ]
        
        created_count = 0
        for template_data in templates:
            # 检查是否已存在同名模板
            existing = db.query(ReminderTemplate).filter(
                ReminderTemplate.name == template_data["name"]
            ).first()
            
            if not existing:
                template = ReminderTemplate(**template_data)
                db.add(template)
                created_count += 1
                print(f"✓ 创建模板: {template_data['name']}")
            else:
                print(f"- 跳过已存在模板: {template_data['name']}")
        
        db.commit()
        
        print(f"\n✅ 完成！共创建 {created_count} 个系统模板")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("开始初始化系统模板...")
    init_system_templates()
