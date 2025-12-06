"""
初始化系统模板数据
"""
import asyncio
from sqlalchemy import select
from app.core.database import async_session_maker
from app.models.reminder_template import ReminderTemplate


async def init_templates():
    """初始化6大场景的系统模板"""
    
    templates = [
        {
            "category": "rent",
            "name": "房租提醒",
            "title_template": "本月房租缴纳提醒",
            "description_template": "记得按时缴纳房租，避免逾期",
            "default_recurrence_type": "monthly",
            "default_recurrence_config": {"day_of_month": 1},
            "default_advance_days": 3,
            "suggested_amount": 2000.00,
            "icon": "home",
            "is_system": True,
            "usage_count": 0
        },
        {
            "category": "health",
            "name": "体检提醒",
            "title_template": "年度体检提醒",
            "description_template": "定期体检，关注健康",
            "default_recurrence_type": "yearly",
            "default_recurrence_config": {"month": 3, "day": 15},
            "default_advance_days": 7,
            "icon": "health",
            "is_system": True,
            "usage_count": 0
        },
        {
            "category": "health",
            "name": "吃药提醒",
            "title_template": "按时服药提醒",
            "description_template": "记得按时服药",
            "default_recurrence_type": "daily",
            "default_recurrence_config": {"interval_days": 1},
            "default_advance_days": 0,
            "icon": "medication",
            "is_system": True,
            "usage_count": 0
        },
        {
            "category": "pet",
            "name": "宠物疫苗",
            "title_template": "宠物疫苗接种提醒",
            "description_template": "带宠物去打疫苗",
            "default_recurrence_type": "yearly",
            "default_recurrence_config": {"month": 6, "day": 1},
            "default_advance_days": 7,
            "icon": "pet",
            "is_system": True,
            "usage_count": 0
        },
        {
            "category": "finance",
            "name": "信用卡还款",
            "title_template": "信用卡还款提醒",
            "description_template": "记得还信用卡，避免逾期",
            "default_recurrence_type": "monthly",
            "default_recurrence_config": {"day_of_month": 20},
            "default_advance_days": 3,
            "icon": "credit_card",
            "is_system": True,
            "usage_count": 0
        },
        {
            "category": "document",
            "name": "证件续期",
            "title_template": "身份证/护照续期提醒",
            "description_template": "证件即将过期，记得续期",
            "default_recurrence_type": "yearly",
            "default_recurrence_config": {"month": 1, "day": 1},
            "default_advance_days": 30,
            "icon": "document",
            "is_system": True,
            "usage_count": 0
        },
        {
            "category": "memorial",
            "name": "生日提醒",
            "title_template": "生日快乐",
            "description_template": "祝你生日快乐！",
            "default_recurrence_type": "yearly",
            "default_recurrence_config": {"month": 1, "day": 1},
            "default_advance_days": 1,
            "icon": "birthday",
            "is_system": True,
            "usage_count": 0
        },
        {
            "category": "memorial",
            "name": "纪念日提醒",
            "title_template": "重要纪念日",
            "description_template": "不要忘记重要的日子",
            "default_recurrence_type": "yearly",
            "default_recurrence_config": {"month": 1, "day": 1},
            "default_advance_days": 1,
            "icon": "anniversary",
            "is_system": True,
            "usage_count": 0
        }
    ]
    
    async with async_session_maker() as session:
        # 检查是否已有模板
        result = await session.execute(
            select(ReminderTemplate).where(ReminderTemplate.is_system == True)
        )
        existing = result.scalars().all()
        
        if existing:
            print(f"⚠️  已存在 {len(existing)} 个系统模板，跳过初始化")
            return
        
        # 批量创建模板
        for template_data in templates:
            template = ReminderTemplate(**template_data)
            session.add(template)
        
        await session.commit()
        print(f"✅ 成功初始化 {len(templates)} 个系统模板")
        
        # 显示创建的模板
        result = await session.execute(
            select(ReminderTemplate).where(ReminderTemplate.is_system == True)
        )
        templates = result.scalars().all()
        
        print("\n📋 系统模板列表:")
        for t in templates:
            print(f"  {t.id}. [{t.category}] {t.name}")


if __name__ == "__main__":
    print("🚀 开始初始化系统模板...")
    asyncio.run(init_templates())
    print("✨ 初始化完成！")
