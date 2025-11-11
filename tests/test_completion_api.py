"""
测试完成记录API
"""
import requests
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def get_token():
    """获取测试用户Token"""
    # 尝试使用测试手机号
    response = requests.post(
        f"{BASE_URL}/users/login",
        json={"phone": "13800138000", "password": "test123"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None

def test_complete_reminder(token, reminder_id=26):
    """测试标记提醒完成"""
    print(f"\n=== 测试完成提醒 ID={reminder_id} ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. 先查看提醒状态
    print("\n1. 查看提醒当前状态:")
    r = requests.get(f"{BASE_URL}/reminders/{reminder_id}", headers=headers)
    if r.status_code == 200:
        reminder = r.json()
        print(f"  - 标题: {reminder['title']}")
        print(f"  - 是否完成: {reminder['is_completed']}")
        print(f"  - 下次提醒: {reminder.get('next_remind_time')}")
        print(f"  - 重复类型: {reminder['recurrence_type']}")
    else:
        print(f"  错误: {r.status_code} - {r.text}")
        return
    
    # 2. 标记完成
    print("\n2. 标记提醒为完成:")
    r = requests.post(
        f"{BASE_URL}/reminders/{reminder_id}/complete",
        headers=headers,
        json={}
    )
    if r.status_code == 200:
        result = r.json()
        print(f"  ✅ 完成成功")
        print(f"  - 是否完成: {result['is_completed']}")
        print(f"  - 完成时间: {result.get('completed_at')}")
        print(f"  - 下次提醒: {result.get('next_remind_time')}")
    else:
        print(f"  ❌ 错误: {r.status_code} - {r.text}")
        return
    
    # 3. 查看完成记录
    print("\n3. 查看完成记录历史:")
    r = requests.get(
        f"{BASE_URL}/reminders/{reminder_id}/completions",
        headers=headers
    )
    if r.status_code == 200:
        completions = r.json()
        print(f"  - 完成次数: {len(completions)}")
        if completions:
            latest = completions[0]
            print(f"  - 最新完成时间: {latest['completed_time']}")
            print(f"  - 计划时间: {latest.get('scheduled_time')}")
            print(f"  - 延迟分钟: {latest['delay_minutes']}")
            print(f"  - 状态: {latest['status']}")
    else:
        print(f"  ❌ 错误: {r.status_code} - {r.text}")
    
    # 4. 取消完成（可选）
    print("\n4. 测试取消完成:")
    r = requests.post(
        f"{BASE_URL}/reminders/{reminder_id}/uncomplete",
        headers=headers
    )
    if r.status_code == 200:
        result = r.json()
        print(f"  ✅ 取消成功")
        print(f"  - 是否完成: {result['is_completed']}")
    else:
        print(f"  ❌ 错误: {r.status_code} - {r.text}")

def test_create_daily_reminder(token):
    """创建测试用的每日提醒"""
    print("\n=== 创建测试提醒 ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    next_remind = (datetime.now() + timedelta(hours=1)).isoformat()
    
    data = {
        "title": "测试每日提醒",
        "content": "用于测试完成功能",
        "category": "other",
        "recurrence_type": "daily",
        "first_remind_time": next_remind,
        "next_remind_time": next_remind,
        "remind_before_minutes": 10,
        "is_active": True
    }
    
    r = requests.post(f"{BASE_URL}/reminders", headers=headers, json=data)
    if r.status_code in [200, 201]:
        reminder = r.json()
        print(f"  ✅ 创建成功 ID={reminder['id']}")
        return reminder['id']
    else:
        print(f"  ❌ 错误: {r.status_code} - {r.text}")
        return None

if __name__ == "__main__":
    print("开始测试完成记录API...\n")
    
    # 获取Token
    token = get_token()
    if not token:
        print("无法获取Token，退出测试")
        exit(1)
    
    print(f"✅ Token获取成功: {token[:50]}...")
    
    # 创建新的测试提醒
    reminder_id = test_create_daily_reminder(token)
    
    if reminder_id:
        # 测试完成流程
        time.sleep(1)
        test_complete_reminder(token, reminder_id)
    
    print("\n✅ 测试完成")
