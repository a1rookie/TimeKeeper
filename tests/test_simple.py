"""
简单的API测试 - 确保服务器保持运行
"""
import requests
import time

BASE_URL = "http://localhost:8000"

print("🚀 启动API测试...")
time.sleep(1)

# 测试登录
print("\n1. 测试登录...")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/users/login",
        json={"phone": "13800138000", "password": "test123"},
        timeout=5
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        token = data["access_token"]
        print("   ✅ 登录成功")
        print(f"   Token: {token[:30]}...")
        
        # 测试获取用户信息
        print("\n2. 测试获取用户信息...")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/v1/users/me", headers=headers, timeout=5)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            user = response.json()
            print(f"   ✅ 用户: {user['phone']}")
            
            # 测试获取提醒列表
            print("\n3. 测试获取提醒列表...")
            response = requests.get(f"{BASE_URL}/api/v1/reminders/", headers=headers, timeout=5)
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                reminders = response.json()
                print(f"   ✅ 提醒数量: {len(reminders)}")
                
                print("\n✅ 所有基础测试通过！")
            else:
                print(f"   ❌ 错误: {response.text}")
        else:
            print(f"   ❌ 错误: {response.text}")
    else:
        print(f"   ❌ 错误: {response.text}")
except Exception as e:
    print(f"   ❌ 异常: {e}")
