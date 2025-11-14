"""
Session Management Test Script
测试会话管理功能：设备互踢、多设备并存
"""
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 测试用户凭证
TEST_PHONE = "13812345678"
TEST_PASSWORD = "Test@123"


def test_login_with_device(device_type: str) -> dict:
    """登录并返回token和响应信息"""
    print(f"\n{'='*60}")
    print(f"📱 正在从 {device_type.upper()} 设备登录...")
    
    response = requests.post(
        f"{BASE_URL}/users/login",
        json={"phone": TEST_PHONE, "password": TEST_PASSWORD},
        headers={"X-Device-Type": device_type}
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data["access_token"]
        print(f"✅ {device_type.upper()} 登录成功")
        print(f"   Token: {token[:50]}...")
        return {"token": token, "device": device_type}
    else:
        print(f"❌ {device_type.upper()} 登录失败: {response.text}")
        return None


def test_get_user_info(session: dict) -> bool:
    """测试token是否有效"""
    device = session["device"]
    token = session["token"]
    
    response = requests.get(
        f"{BASE_URL}/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ {device.upper()} token有效 - 用户: {data['phone']}")
        return True
    elif response.status_code == 401:
        error = response.json()
        print(f"   ❌ {device.upper()} token失效 - {error.get('detail', '未知错误')}")
        return False
    else:
        print(f"   ⚠️  {device.upper()} 请求异常 - {response.status_code}")
        return False


def test_get_active_sessions(token: str):
    """查询当前活跃会话"""
    print(f"\n{'='*60}")
    print("📋 查询活跃会话...")
    
    response = requests.get(
        f"{BASE_URL}/users/sessions",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        sessions = response.json()
        print(f"✅ 当前活跃会话数: {len(sessions)}")
        for device_type, info in sessions.items():
            print(f"   - {device_type.upper()}: JTI={info['jti'][:20]}..., "
                  f"剩余{info['expires_in_seconds']}秒")
    else:
        print(f"❌ 查询失败: {response.text}")


def test_logout_device(token: str, device_type: str):
    """单设备登出"""
    print(f"\n{'='*60}")
    print(f"🚪 正在登出 {device_type.upper()} 设备...")
    
    response = requests.post(
        f"{BASE_URL}/users/logout",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Device-Type": device_type
        }
    )
    
    if response.status_code == 200:
        print(f"✅ {device_type.upper()} 登出成功")
    else:
        print(f"❌ {device_type.upper()} 登出失败: {response.text}")


def test_logout_all(token: str):
    """全局登出"""
    print(f"\n{'='*60}")
    print("🚪 正在全局登出所有设备...")
    
    response = requests.post(
        f"{BASE_URL}/users/logout/all",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 全局登出成功，共注销 {data.get('revoked_count', 0)} 个设备")
    else:
        print(f"❌ 全局登出失败: {response.text}")


def main():
    print("\n" + "="*60)
    print("🧪 TimeKeeper 会话管理测试")
    print("="*60)
    
    # 测试1: 同设备类型互踢
    print("\n【测试1: 同设备类型互踢（Web设备）】")
    web_session_1 = test_login_with_device("web")
    input("按Enter继续...")
    
    print("\n验证第一个Web token是否有效:")
    test_get_user_info(web_session_1)
    input("按Enter继续...")
    
    web_session_2 = test_login_with_device("web")
    input("按Enter继续...")
    
    print("\n验证第一个Web token是否被踢掉:")
    test_get_user_info(web_session_1)  # 应该失败（被踢掉）
    
    print("\n验证第二个Web token是否有效:")
    test_get_user_info(web_session_2)  # 应该成功
    input("按Enter继续...")
    
    # 测试2: 不同设备类型共存
    print("\n【测试2: 不同设备类型共存】")
    ios_session = test_login_with_device("ios")
    input("按Enter继续...")
    
    android_session = test_login_with_device("android")
    input("按Enter继续...")
    
    print("\n验证所有设备token是否都有效:")
    test_get_user_info(web_session_2)  # 仍然有效
    test_get_user_info(ios_session)     # 新登录，有效
    test_get_user_info(android_session) # 新登录，有效
    input("按Enter继续...")
    
    # 测试3: 查询活跃会话
    test_get_active_sessions(web_session_2["token"])
    input("按Enter继续...")
    
    # 测试4: 单设备登出
    print("\n【测试3: 单设备登出】")
    test_logout_device(ios_session["token"], "ios")
    input("按Enter继续...")
    
    print("\n验证iOS token是否失效:")
    test_get_user_info(ios_session)  # 应该失败
    
    print("\n验证其他设备token是否仍有效:")
    test_get_user_info(web_session_2)    # 仍然有效
    test_get_user_info(android_session)  # 仍然有效
    input("按Enter继续...")
    
    # 测试5: 全局登出
    print("\n【测试4: 全局登出】")
    test_logout_all(web_session_2["token"])
    input("按Enter继续...")
    
    print("\n验证所有token是否都失效:")
    test_get_user_info(web_session_2)    # 应该失败
    test_get_user_info(android_session)  # 应该失败
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试中断")
    except Exception as e:
        print(f"\n\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
