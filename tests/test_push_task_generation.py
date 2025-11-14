"""
测试PushTask API和自动生成
"""
import sys
sys.path.insert(0, r"d:\pygithub\TimeKeeper\TimeKeeper")

from fastapi.testclient import TestClient
from main import app
from datetime import datetime, timedelta

def test_push_task_generation():
    """测试创建提醒时自动生成推送任务"""
    client = TestClient(app)
    
    print("="*80)
    print("PushTask Generation and API Validation")
    print("="*80)
    
    # 1. 注册并登录
    timestamp = datetime.now().timestamp()
    register_data = {
        "phone": f"138{int(timestamp % 100000000)}",
        "password": "Password123!",
        "nickname": f"PushTestUser{int(timestamp)}"
    }
    
    register_response = client.post("/api/v1/users/register", json=register_data)
    print(f"\n[1] User Registration: {register_response.status_code}")
    
    login_data = {
        "phone": register_data["phone"],
        "password": register_data["password"]
    }
    login_response = client.post("/api/v1/users/login", json=login_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"[2] User Login: {login_response.status_code}")
    
    # 2. 创建提醒（应自动生成PushTask）
    print("\n" + "-"*80)
    print("Creating Reminder with Auto PushTask Generation")
    print("-"*80)
    
    reminder_data = {
        "title": "Important Meeting",
        "description": "Quarterly review meeting",
        "category": "other",
        "recurrence_type": "weekly",
        "recurrence_config": {"weekday": 1},  # Monday
        "first_remind_time": (datetime.now() + timedelta(hours=2)).isoformat(),
        "remind_channels": ["app", "sms"],
        "advance_minutes": 30,
        "priority": 2
    }
    
    create_response = client.post("/api/v1/reminders/", json=reminder_data, headers=headers)
    print(f"Reminder Created: {create_response.status_code}")
    
    if create_response.status_code not in [200, 201]:
        print(f"ERROR: {create_response.json()}")
        return False
    
    reminder = create_response.json()
    print(f"Reminder ID: {reminder['id']}")
    print(f"Reminder Title: {reminder['title']}")
    print(f"Channels: {reminder['remind_channels']}")
    
    # 3. 查询PushTask列表
    print("\n" + "-"*80)
    print("Querying PushTask List")
    print("-"*80)
    
    list_response = client.get("/api/v1/push-tasks/", headers=headers)
    print(f"Status Code: {list_response.status_code}")
    
    if list_response.status_code != 200:
        print(f"ERROR: {list_response.json()}")
        return False
    
    result = list_response.json()
    print(f"\nTotal PushTasks: {result.get('total', 0)}")
    
    if result.get('total', 0) == 0:
        print("WARNING: No PushTask generated automatically!")
        print("Expected: At least 1 PushTask for the created reminder")
        return False
    
    tasks = result.get('tasks', [])
    print(f"Tasks Retrieved: {len(tasks)}")
    
    for i, task in enumerate(tasks, 1):
        print(f"\nPushTask #{i}:")
        print(f"  ID: {task['id']}")
        print(f"  Reminder ID: {task['reminder_id']}")
        print(f"  Title: {task['title']}")
        print(f"  Channels: {task['channels']}")
        print(f"  Status: {task['status']}")
        print(f"  Priority: {task.get('priority', 'N/A')}")
        print(f"  Scheduled Time: {task['scheduled_time']}")
        print(f"  Retry Count: {task.get('retry_count', 0)}")
        print(f"  Max Retries: {task.get('max_retries', 3)}")
    
    # 4. 按Reminder ID筛选
    print("\n" + "-"*80)
    print(f"Filtering PushTasks by Reminder ID: {reminder['id']}")
    print("-"*80)
    
    filter_response = client.get(
        f"/api/v1/push-tasks/?reminder_id={reminder['id']}", 
        headers=headers
    )
    print(f"Status Code: {filter_response.status_code}")
    
    if filter_response.status_code != 200:
        print(f"ERROR: {filter_response.json()}")
        return False
    
    filtered_result = filter_response.json()
    print(f"Filtered Tasks: {filtered_result.get('total', 0)}")
    
    # 5. 按状态筛选
    print("\n" + "-"*80)
    print("Filtering PushTasks by Status: PENDING")
    print("-"*80)
    
    status_response = client.get(
        "/api/v1/push-tasks/?status=pending", 
        headers=headers
    )
    print(f"Status Code: {status_response.status_code}")
    
    if status_response.status_code != 200:
        print(f"ERROR: {status_response.json()}")
        return False
    
    status_result = status_response.json()
    print(f"Pending Tasks: {status_result.get('total', 0)}")
    
    # 6. 获取单个PushTask详情
    if tasks:
        task_id = tasks[0]['id']
        print("\n" + "-"*80)
        print(f"Getting PushTask Details: ID={task_id}")
        print("-"*80)
        
        detail_response = client.get(f"/api/v1/push-tasks/{task_id}", headers=headers)
        print(f"Status Code: {detail_response.status_code}")
        
        if detail_response.status_code != 200:
            print(f"ERROR: {detail_response.json()}")
            return False
        
        task_detail = detail_response.json()
        print(f"Task ID: {task_detail['id']}")
        print(f"User ID: {task_detail['user_id']}")
        print(f"Reminder ID: {task_detail['reminder_id']}")
        print(f"Content: {task_detail.get('content', 'N/A')}")
    
    # Summary
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80)
    print(f"✓ Reminder Created: {reminder['id']}")
    print(f"✓ PushTasks Generated: {result.get('total', 0)}")
    print("✓ List API Working: Yes")
    print("✓ Filter by Reminder ID: Yes")
    print("✓ Filter by Status: Yes")
    print("✓ Get Task Details: Yes")
    print("\nAll PushTask Features Working!")
    print("="*80)
    
    return True

if __name__ == "__main__":
    try:
        success = test_push_task_generation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
