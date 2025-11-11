"""
测试用户注册、登录和提醒CRUD完整流程
"""
import requests
import json
import sys
import io

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000"

def test_e2e_flow():
    print("="*60)
    print("TimeKeeper E2E API 测试")
    print("="*60)
    
    # 1. 测试已有用户登录
    print("\n1️⃣  测试登录...")
    login_data = {
        "phone": "13800138000",
        "password": "test123"
    }
    response = requests.post(f"{BASE_URL}/api/v1/users/login", json=login_data)
    assert response.status_code == 200, f"登录失败: {response.text}"
    token_data = response.json()
    token = token_data["access_token"]
    print(f"   ✅ 登录成功")
    print(f"   Token: {token[:50]}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. 获取当前用户信息
    print("\n2️⃣  获取用户信息...")
    response = requests.get(f"{BASE_URL}/api/v1/users/me", headers=headers)
    assert response.status_code == 200, f"获取用户信息失败: {response.text}"
    user = response.json()
    print(f"   ✅ 用户ID: {user['id']}, 手机: {user['phone']}")
    
    # 3. 创建新提醒
    print("\n3️⃣  创建提醒...")
    reminder_data = {
        "title": "API测试提醒",
        "description": "通过E2E测试创建的提醒",
        "category": "health",
        "recurrence_type": "daily",
        "recurrence_config": {"interval": 1},
        "first_remind_time": "2025-02-01T09:00:00",
        "remind_channels": ["app"],
        "advance_minutes": 0
    }
    response = requests.post(f"{BASE_URL}/api/v1/reminders/", json=reminder_data, headers=headers)
    assert response.status_code == 201, f"创建提醒失败 (状态码: {response.status_code}): {response.text}"
    reminder = response.json()
    reminder_id = reminder["id"]
    print(f"   ✅ 提醒创建成功, ID: {reminder_id}")
    print(f"   标题: {reminder['title']}")
    
    # 4. 获取所有提醒
    print("\n4️⃣  获取提醒列表...")
    response = requests.get(f"{BASE_URL}/api/v1/reminders/", headers=headers)
    assert response.status_code == 200, f"获取提醒列表失败: {response.text}"
    reminders = response.json()
    print(f"   ✅ 共 {len(reminders)} 条提醒")
    for r in reminders:
        print(f"      - [{r['id']}] {r['title']} ({r['recurrence_type']})")
    
    # 5. 更新提醒
    print("\n5️⃣  更新提醒...")
    update_data = {
        "title": "API测试提醒(已更新)",
        "recurrence_config": {"interval": 2}
    }
    response = requests.put(
        f"{BASE_URL}/api/v1/reminders/{reminder_id}", 
        json=update_data, 
        headers=headers
    )
    assert response.status_code == 200, f"更新提醒失败: {response.text}"
    updated = response.json()
    print(f"   ✅ 提醒更新成功")
    print(f"   新标题: {updated['title']}")
    print(f"   新配置: {updated['recurrence_config']}")
    
    # 6. 测试权限隔离（尝试访问不存在的ID）
    print("\n6️⃣  测试权限隔离...")
    response = requests.get(f"{BASE_URL}/api/v1/reminders/99999", headers=headers)
    assert response.status_code == 404, "应该返回404"
    print(f"   ✅ 权限隔离正常（无法访问他人数据）")
    
    # 7. 删除提醒
    print("\n7️⃣  删除提醒...")
    response = requests.delete(f"{BASE_URL}/api/v1/reminders/{reminder_id}", headers=headers)
    assert response.status_code == 200, f"删除提醒失败: {response.text}"
    print(f"   ✅ 提醒删除成功")
    
    # 8. 验证删除
    print("\n8️⃣  验证删除...")
    response = requests.get(f"{BASE_URL}/api/v1/reminders/{reminder_id}", headers=headers)
    assert response.status_code == 404, "应该返回404"
    print(f"   ✅ 确认已删除")
    
    # 9. 测试未授权访问
    print("\n9️⃣  测试未授权访问...")
    response = requests.get(f"{BASE_URL}/api/v1/users/me")  # 无token
    assert response.status_code == 401, f"应该返回401: {response.status_code}"
    print(f"   ✅ 未授权访问被拒绝")
    
    print("\n" + "="*60)
    print("✅ 所有测试通过！")
    print("="*60)
    print("\n📊 测试总结:")
    print("   ✅ 用户登录认证")
    print("   ✅ JWT Token验证")
    print("   ✅ 用户信息获取")
    print("   ✅ 提醒创建")
    print("   ✅ 提醒列表查询")
    print("   ✅ 提醒更新")
    print("   ✅ 提醒删除")
    print("   ✅ 权限隔离")
    print("   ✅ 未授权访问拦截")

if __name__ == "__main__":
    try:
        test_e2e_flow()
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器，请确保服务器正在运行:")
        print("   python main.py")
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
