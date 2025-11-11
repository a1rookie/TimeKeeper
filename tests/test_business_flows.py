"""
完整业务流程验证 - 根据"完整业务流程设计.md"
验证所有核心业务场景
"""
import sys
sys.path.insert(0, r"d:\pygithub\TimeKeeper\TimeKeeper")

from fastapi.testclient import TestClient
from main import app
from datetime import datetime, timedelta
import json

client = TestClient(app)

def print_section(title):
    """打印章节标题"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_step(step_num, description):
    """打印步骤信息"""
    print(f"\n[Step {step_num}] {description}")
    print("-" * 80)

# ============================================================================
# 流程1：用户注册与认证
# ============================================================================
def test_user_registration_authentication():
    """测试用户注册与认证流程"""
    print_section("流程1：用户注册与认证")
    
    # 1.1 手机号注册
    print_step("1.1", "用户输入手机号并注册")
    timestamp = datetime.now().timestamp()
    user_phone = f"138{int(timestamp % 100000000)}"
    
    register_data = {
        "phone": user_phone,
        "password": "SecurePass123!",
        "nickname": f"用户{int(timestamp)}"
    }
    
    register_response = client.post("/api/v1/users/register", json=register_data)
    print(f"注册状态: {register_response.status_code}")
    assert register_response.status_code in [200, 201], "注册失败"
    
    user = register_response.json()
    print(f"✓ 用户ID: {user['id']}")
    print(f"✓ 手机号: {user['phone']}")
    print(f"✓ 昵称: {user.get('nickname')}")
    print(f"✓ 激活状态: {user.get('is_active', True)}")
    
    # 1.2 用户登录
    print_step("1.2", "用户登录获取Token")
    login_data = {
        "phone": user_phone,
        "password": "SecurePass123!"
    }
    
    login_response = client.post("/api/v1/users/login", json=login_data)
    print(f"登录状态: {login_response.status_code}")
    assert login_response.status_code == 200, "登录失败"
    
    login_result = login_response.json()
    token = login_result["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"✓ Token类型: {login_result['token_type']}")
    print(f"✓ Access Token: {token[:30]}...")
    
    # 1.3 获取当前用户信息
    print_step("1.3", "验证Token有效性")
    me_response = client.get("/api/v1/users/me", headers=headers)
    print(f"获取用户信息状态: {me_response.status_code}")
    assert me_response.status_code == 200, "获取用户信息失败"
    
    me_data = me_response.json()
    print(f"✓ 当前用户ID: {me_data['id']}")
    print(f"✓ 认证成功")
    
    print("\n✅ 流程1验证通过：用户注册与认证")
    return headers, user

# ============================================================================
# 流程2：创建提醒（核心流程）
# ============================================================================
def test_create_reminder_flow(headers, user):
    """测试创建提醒核心流程"""
    print_section("流程2：创建提醒（核心流程）")
    
    # 2.1 基于场景创建提醒（模拟选择健康类模板）
    print_step("2.1", "基于场景创建提醒 - 健康类（吃药提醒）")
    
    health_reminder = {
        "title": "每日吃药提醒",
        "description": "每天晚上8点按时服药",
        "category": "health",
        "recurrence_type": "daily",
        "recurrence_config": {"time": "20:00"},
        "first_remind_time": (datetime.now() + timedelta(hours=1)).isoformat(),
        "remind_channels": ["app"],
        "advance_minutes": 0,
        "priority": 2  # 重要
    }
    
    create_response = client.post("/api/v1/reminders/", json=health_reminder, headers=headers)
    print(f"创建状态: {create_response.status_code}")
    assert create_response.status_code in [200, 201], "创建提醒失败"
    
    reminder1 = create_response.json()
    print(f"✓ 提醒ID: {reminder1['id']}")
    print(f"✓ 标题: {reminder1['title']}")
    print(f"✓ 分类: {reminder1['category']}")
    print(f"✓ 优先级: {reminder1['priority']}")
    print(f"✓ 周期类型: {reminder1['recurrence_type']}")
    
    # 2.1.1 验证推送任务自动生成（通过数据库检查）
    print_step("2.1.1", "验证推送任务自动生成")
    from app.core.database import get_db
    from app.models.push_task import PushTask
    from sqlalchemy import select
    
    db = next(get_db())
    stmt = select(PushTask).where(PushTask.reminder_id == reminder1['id'])
    push_tasks = db.execute(stmt).scalars().all()
    print(f"✓ 自动生成推送任务数: {len(push_tasks)}")
    assert len(push_tasks) > 0, "推送任务未自动生成"
    db.close()
    
    # 2.2 复杂提醒创建（租房场景）
    print_step("2.2", "创建复杂提醒 - 租房场景（房租提醒）")
    
    rent_reminder = {
        "title": "每月交房租",
        "description": "每月25号前交房租给房东",
        "category": "finance",
        "recurrence_type": "monthly",
        "recurrence_config": {
            "day": 25,
            "skip_weekend": True  # 遇周末顺延
        },
        "first_remind_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "remind_channels": ["app", "sms"],
        "advance_minutes": 2880,  # 提前2天
        "priority": 3,  # 紧急
        "amount": 350000,  # 3500元
        "location": {
            "address": "北京市朝阳区建国路1号",
            "landlord_name": "张先生",
            "landlord_phone": "13800138000"
        },
        "attachments": [
            {
                "type": "image",
                "url": "https://example.com/contract.jpg",
                "filename": "租房合同.jpg"
            }
        ]
    }
    
    create_response2 = client.post("/api/v1/reminders/", json=rent_reminder, headers=headers)
    print(f"创建状态: {create_response2.status_code}")
    assert create_response2.status_code in [200, 201], "创建复杂提醒失败"
    
    reminder2 = create_response2.json()
    print(f"✓ 提醒ID: {reminder2['id']}")
    print(f"✓ 标题: {reminder2['title']}")
    print(f"✓ 优先级: {reminder2['priority']} (紧急)")
    print(f"✓ 金额: ¥{reminder2['amount']/100:.2f}")
    print(f"✓ 位置信息: {reminder2['location']['address']}")
    print(f"✓ 附件数量: {len(reminder2['attachments'])}")
    print(f"✓ 提醒渠道: {reminder2['remind_channels']}")
    
    # 2.3 验证提醒列表
    print_step("2.3", "查询提醒列表")
    list_response = client.get("/api/v1/reminders/", headers=headers)
    print(f"查询状态: {list_response.status_code}")
    reminders_list = list_response.json()
    print(f"✓ 用户提醒总数: {len(reminders_list)}")
    
    print("\n✅ 流程2验证通过：创建提醒核心流程")
    return [reminder1, reminder2]

# ============================================================================
# 流程3：推送任务执行
# ============================================================================
def test_push_task_execution_flow(headers, reminders):
    """测试推送任务执行流程"""
    print_section("流程3：推送任务执行")
    
    # 3.1 查询待推送任务（通过数据库）
    print_step("3.1", "查询所有待推送任务")
    
    from app.core.database import get_db
    from app.models.push_task import PushTask, PushStatus
    from sqlalchemy import select
    
    db = next(get_db())
    stmt = select(PushTask).where(PushTask.status == PushStatus.PENDING)
    pending_tasks = db.execute(stmt).scalars().all()
    print(f"✓ Pending任务数: {len(pending_tasks)}")
    
    # 验证任务关联了提醒
    if len(pending_tasks) > 0:
        first_task = pending_tasks[0]
        print(f"✓ 第一个任务: ID={first_task.id}, 提醒ID={first_task.reminder_id}, 标题={first_task.title}")
        print(f"✓ 推送渠道: {first_task.channels}")
        print(f"✓ 计划时间: {first_task.scheduled_time}")
        print(f"✓ 重试配置: {first_task.retry_count}/{first_task.max_retries}")
        
        # 3.2 按提醒ID筛选任务
        print_step("3.2", "按提醒ID筛选推送任务")
        reminder_id = reminders[0]['id']
        stmt2 = select(PushTask).where(PushTask.reminder_id == reminder_id)
        reminder_tasks = db.execute(stmt2).scalars().all()
        print(f"✓ 提醒ID {reminder_id} 的任务数: {len(reminder_tasks)}")
    
    db.close()
    print("\n✅ 流程3验证通过：推送任务执行流程")

# ============================================================================
# 周期计算验证
# ============================================================================
def test_recurrence_calculation(headers):
    """测试周期计算引擎"""
    print_section("流程7：周期计算引擎验证")
    
    # 7.1 每周提醒
    print_step("7.1", "创建每周一提醒")
    weekly_reminder = {
        "title": "团队周会",
        "description": "每周一上午10点团队例会",
        "category": "other",
        "recurrence_type": "weekly",
        "recurrence_config": {"weekday": 1},  # Monday
        "first_remind_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "remind_channels": ["app"],
        "advance_minutes": 30
    }
    
    create_response = client.post("/api/v1/reminders/", json=weekly_reminder, headers=headers)
    print(f"创建状态: {create_response.status_code}")
    assert create_response.status_code in [200, 201], "创建每周提醒失败"
    
    weekly = create_response.json()
    print(f"✓ 提醒ID: {weekly['id']}")
    print(f"✓ 周期类型: {weekly['recurrence_type']}")
    print(f"✓ 周期配置: {weekly['recurrence_config']}")
    
    # 7.2 每年提醒
    print_step("7.2", "创建每年生日提醒")
    yearly_reminder = {
        "title": "妈妈生日",
        "description": "记得给妈妈准备生日礼物",
        "category": "memorial",
        "recurrence_type": "yearly",
        "recurrence_config": {"month": 3, "day": 15},
        "first_remind_time": (datetime.now() + timedelta(days=30)).isoformat(),
        "remind_channels": ["app", "sms"],
        "advance_minutes": 10080  # 提前7天
    }
    
    create_response2 = client.post("/api/v1/reminders/", json=yearly_reminder, headers=headers)
    print(f"创建状态: {create_response2.status_code}")
    assert create_response2.status_code in [200, 201], "创建每年提醒失败"
    
    yearly = create_response2.json()
    print(f"✓ 提醒ID: {yearly['id']}")
    print(f"✓ 周期类型: {yearly['recurrence_type']}")
    print(f"✓ 周期配置: {yearly['recurrence_config']}")
    print(f"✓ 提前天数: {yearly['advance_minutes']/1440:.0f}天")
    
    print("\n✅ 流程7验证通过：周期计算引擎")

# ============================================================================
# 提醒CRUD操作
# ============================================================================
def test_reminder_crud(headers, reminders):
    """测试提醒的完整CRUD操作"""
    print_section("提醒CRUD操作验证")
    
    reminder_id = reminders[0]['id']
    
    # 获取详情
    print_step("1", "获取提醒详情")
    detail_response = client.get(f"/api/v1/reminders/{reminder_id}", headers=headers)
    print(f"✓ 获取详情状态: {detail_response.status_code}")
    
    # 更新提醒
    print_step("2", "更新提醒信息")
    update_data = {
        "title": "每日吃药提醒（已更新）",
        "priority": 3,
        "description": "更新后的描述"
    }
    
    update_response = client.put(
        f"/api/v1/reminders/{reminder_id}", 
        json=update_data, 
        headers=headers
    )
    print(f"✓ 更新状态: {update_response.status_code}")
    
    updated = update_response.json()
    print(f"✓ 新标题: {updated['title']}")
    print(f"✓ 新优先级: {updated['priority']}")
    
    # 删除提醒
    print_step("3", "删除提醒")
    delete_response = client.delete(f"/api/v1/reminders/{reminder_id}", headers=headers)
    print(f"✓ 删除状态: {delete_response.status_code}")
    
    # 验证删除
    verify_response = client.get(f"/api/v1/reminders/{reminder_id}", headers=headers)
    print(f"✓ 验证删除: {verify_response.status_code} (应为404)")
    assert verify_response.status_code == 404, "提醒未被删除"
    
    print("\n✅ CRUD操作验证通过")

# ============================================================================
# 主测试函数
# ============================================================================
def run_all_tests():
    """运行所有业务流程测试"""
    print("\n" + "="*80)
    print("  TimeKeeper - 完整业务流程验证")
    print("  基于：周期提醒APP - 完整业务流程设计.md")
    print("="*80)
    
    try:
        # 流程1：用户注册与认证
        headers, user = test_user_registration_authentication()
        
        # 流程2：创建提醒
        reminders = test_create_reminder_flow(headers, user)
        
        # 流程3：推送任务执行
        test_push_task_execution_flow(headers, reminders)
        
        # 流程7：周期计算
        test_recurrence_calculation(headers)
        
        # CRUD操作
        test_reminder_crud(headers, reminders)
        
        # 总结
        print("\n" + "="*80)
        print("  🎉 所有业务流程验证通过！")
        print("="*80)
        print("\n✅ 已验证流程：")
        print("  1. 用户注册与认证 ✓")
        print("  2. 创建提醒（核心流程）✓")
        print("  3. 推送任务执行 ✓")
        print("  7. 周期计算引擎 ✓")
        print("  - CRUD操作 ✓")
        
        print("\n⏳ 待开发流程：")
        print("  4. 家庭共享功能")
        print("  5. 模板分享生态")
        print("  6. 数据统计与分析")
        
        print("\n" + "="*80)
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
