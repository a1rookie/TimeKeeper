"""
测试推送任务API端点
Test Push Task API Endpoints
"""

import asyncio
import httpx
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# 测试用户信息
test_user = {
    "username": "testuser_push",
    "email": "testuser_push@example.com",
    "password": "TestPass123!"
}


async def test_push_task_flow():
    """测试完整的推送任务流程"""
    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("测试推送任务 API 流程")
        print("=" * 60)
        
        # Step 1: 注册用户
        print("\n1. 注册测试用户...")
        try:
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/users/register",
                json=test_user
            )
            if response.status_code == 409:
                print("   用户已存在，跳过注册")
            else:
                response.raise_for_status()
                print(f"   ✓ 注册成功: {response.json()['username']}")
        except Exception as e:
            print(f"   ✗ 注册失败: {e}")
            return
        
        # Step 2: 登录获取token
        print("\n2. 用户登录...")
        try:
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/users/login",
                data={
                    "username": test_user["username"],
                    "password": test_user["password"]
                }
            )
            response.raise_for_status()
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("   ✓ 登录成功，获得token")
        except Exception as e:
            print(f"   ✗ 登录失败: {e}")
            return
        
        # Step 3: 创建提醒
        print("\n3. 创建测试提醒...")
        reminder_data = {
            "title": "推送测试提醒",
            "description": "用于测试推送功能的提醒",
            "reminder_time": (datetime.now() + timedelta(minutes=5)).isoformat(),
            "recurrence_rule": "DAILY",
            "is_active": True
        }
        try:
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/reminders/",
                json=reminder_data,
                headers=headers
            )
            response.raise_for_status()
            reminder_id = response.json()["id"]
            print(f"   ✓ 提醒创建成功，ID: {reminder_id}")
        except Exception as e:
            print(f"   ✗ 提醒创建失败: {e}")
            return
        
        # Step 4: 创建推送任务
        print("\n4. 创建推送任务...")
        push_task_data = {
            "reminder_id": reminder_id,
            "scheduled_time": (datetime.now() + timedelta(minutes=2)).isoformat()
        }
        try:
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/push-tasks/",
                json=push_task_data,
                headers=headers
            )
            response.raise_for_status()
            task = response.json()
            task_id = task["id"]
            print("   ✓ 推送任务创建成功")
            print(f"     - 任务ID: {task_id}")
            print(f"     - 状态: {task['status']}")
            print(f"     - 计划时间: {task['scheduled_time']}")
        except Exception as e:
            print(f"   ✗ 推送任务创建失败: {e}")
            return
        
        # Step 5: 查询推送任务
        print("\n5. 查询推送任务...")
        try:
            response = await client.get(
                f"{BASE_URL}{API_PREFIX}/push-tasks/{task_id}",
                headers=headers
            )
            response.raise_for_status()
            task = response.json()
            print("   ✓ 查询成功")
            print(f"     - 标题: {task['title']}")
            print(f"     - 内容: {task['content']}")
            print(f"     - 推送渠道: {task['channels']}")
        except Exception as e:
            print(f"   ✗ 查询失败: {e}")
        
        # Step 6: 获取推送任务列表
        print("\n6. 获取推送任务列表...")
        try:
            response = await client.get(
                f"{BASE_URL}{API_PREFIX}/push-tasks/",
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            print(f"   ✓ 查询成功，共 {result['total']} 个任务")
            for task in result['tasks']:
                print(f"     - [{task['status']}] {task['title']}")
        except Exception as e:
            print(f"   ✗ 查询失败: {e}")
        
        # Step 7: 获取推送统计
        print("\n7. 获取推送统计...")
        try:
            response = await client.get(
                f"{BASE_URL}{API_PREFIX}/push-tasks/stats/summary",
                headers=headers
            )
            response.raise_for_status()
            stats = response.json()
            print("   ✓ 统计信息:")
            print(f"     - 总任务数: {stats['total']}")
            print(f"     - 待发送: {stats['pending']}")
            print(f"     - 已发送: {stats['sent']}")
            print(f"     - 失败: {stats['failed']}")
            print(f"     - 已取消: {stats['cancelled']}")
            print(f"     - 成功率: {stats['success_rate']}%")
        except Exception as e:
            print(f"   ✗ 获取统计失败: {e}")
        
        # Step 8: 更新推送任务
        print("\n8. 更新推送任务时间...")
        update_data = {
            "scheduled_time": (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        try:
            response = await client.put(
                f"{BASE_URL}{API_PREFIX}/push-tasks/{task_id}",
                json=update_data,
                headers=headers
            )
            response.raise_for_status()
            task = response.json()
            print(f"   ✓ 更新成功，新时间: {task['scheduled_time']}")
        except Exception as e:
            print(f"   ✗ 更新失败: {e}")
        
        # Step 9: 取消推送任务
        print("\n9. 取消推送任务...")
        try:
            response = await client.delete(
                f"{BASE_URL}{API_PREFIX}/push-tasks/{task_id}",
                headers=headers
            )
            response.raise_for_status()
            print("   ✓ 取消成功")
        except Exception as e:
            print(f"   ✗ 取消失败: {e}")
        
        # Step 10: 验证取消状态
        print("\n10. 验证取消状态...")
        try:
            response = await client.get(
                f"{BASE_URL}{API_PREFIX}/push-tasks/{task_id}",
                headers=headers
            )
            response.raise_for_status()
            task = response.json()
            status = task['status']
            if status == "CANCELLED":
                print(f"   ✓ 状态正确: {status}")
            else:
                print(f"   ✗ 状态错误: {status}")
        except Exception as e:
            print(f"   ✗ 验证失败: {e}")
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_push_task_flow())
