"""
Quick Session Test - Auto run without user input
快速自动化测试会话管理
"""
import requests
import time

BASE_URL = "http://localhost:8000/api/v1"
TEST_PHONE = "13812345678"
TEST_PASSWORD = "Test@123"


def login(device_type: str):
    """Login and return token"""
    print(f"\nLogin from {device_type.upper()}...")
    response = requests.post(
        f"{BASE_URL}/users/login",
        json={"phone": TEST_PHONE, "password": TEST_PASSWORD},
        headers={"X-Device-Type": device_type}
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data["access_token"]
        print(f"   OK - Token: ...{token[-20:]}")
        return token
    else:
        print(f"   FAIL: {response.status_code}")
        return None


def check_token(token: str, label: str):
    """Check if token is valid"""
    response = requests.get(
        f"{BASE_URL}/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   OK {label} - valid (user: {data['phone']})")
        return True
    elif response.status_code == 401:
        print(f"   FAIL {label} - invalid ({response.json().get('detail', 'unknown')})")
        return False
    else:
        print(f"   WARN {label} - error ({response.status_code})")
        return False


def get_sessions(token: str):
    """Query active sessions"""
    print(f"\nQuery sessions...")
    response = requests.get(
        f"{BASE_URL}/users/sessions",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        sessions = response.json()
        print(f"   OK - {len(sessions)} sessions:")
        for device, info in sessions.items():
            print(f"      - {device.upper()}: {info['expires_in_seconds']}s left")
        return sessions
    else:
        print(f"   FAIL: {response.status_code}")
        return None


def main():
    print("="*70)
    print("TimeKeeper Session Management Test")
    print("="*70)
    
    # 测试1: 同设备互踢
    print("\n【测试1: 同设备类型互踢】")
    print("-" * 70)
    
    web1 = login("web")
    time.sleep(0.5)
    
    print("\n验证 Web Token #1:")
    check_token(web1, "Web #1")
    time.sleep(0.5)
    
    web2 = login("web")  # 应该踢掉 web1
    time.sleep(0.5)
    
    print("\n验证 Web Token #1 是否被踢:")
    check_token(web1, "Web #1")
    
    print("\n验证 Web Token #2 是否有效:")
    check_token(web2, "Web #2")
    
    # 测试2: 多设备共存
    print("\n" + "="*70)
    print("【测试2: 不同设备类型共存】")
    print("-" * 70)
    
    ios = login("ios")
    time.sleep(0.5)
    
    android = login("android")
    time.sleep(0.5)
    
    print("\n验证所有设备 token:")
    check_token(web2, "Web")
    check_token(ios, "iOS")
    check_token(android, "Android")
    
    # 测试3: 查询会话
    print("\n" + "="*70)
    print("【测试3: 查询活跃会话】")
    print("-" * 70)
    get_sessions(web2)
    
    # 测试4: 单设备登出
    print("\n" + "="*70)
    print("【测试4: 单设备登出 (iOS)】")
    print("-" * 70)
    
    response = requests.post(
        f"{BASE_URL}/users/logout",
        headers={
            "Authorization": f"Bearer {ios}",
            "X-Device-Type": "ios"
        }
    )
    
    if response.status_code == 200:
        print("   ✅ iOS 登出成功")
    else:
        print(f"   ❌ iOS 登出失败: {response.status_code}")
    
    time.sleep(0.5)
    
    print("\n验证 iOS token 是否失效:")
    check_token(ios, "iOS")
    
    print("\n验证其他设备是否仍有效:")
    check_token(web2, "Web")
    check_token(android, "Android")
    
    # 测试5: 全局登出
    print("\n" + "="*70)
    print("【测试5: 全局登出所有设备】")
    print("-" * 70)
    
    response = requests.post(
        f"{BASE_URL}/users/logout/all",
        headers={"Authorization": f"Bearer {web2}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 全局登出成功，注销 {data.get('revoked_count', 0)} 个设备")
    else:
        print(f"   ❌ 全局登出失败: {response.status_code}")
    
    time.sleep(0.5)
    
    print("\n验证所有 token 是否都失效:")
    check_token(web2, "Web")
    check_token(android, "Android")
    
    print("\n" + "="*70)
    print("Test completed!")
    print("="*70)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器，请确保服务器正在运行:")
        print("   uv run uvicorn main:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
