"""
测试短信验证码登录流程
"""
import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_sms_login_flow():
    """测试完整的短信验证码登录流程"""
    
    # 测试用的手机号（假设已注册）
    phone = "18738710275"
    
    print("\n" + "="*70)
    print("📱 短信验证码登录测试")
    print("="*70)
    
    # 步骤1：发送登录验证码
    print("\n[步骤1] 发送登录验证码...")
    try:
        response = requests.post(
            f"{BASE_URL}/users/send-sms-code",
            json={
                "phone": phone,
                "purpose": "login"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 验证码已发送")
            print(f"   手机号: {phone}")
            print("   用途: 登录")
            print(f"   有效期: {data.get('expires_in', 300)} 秒")
        else:
            error = response.json()
            print(f"❌ 发送失败: {error.get('detail', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        print("提示: 请确保FastAPI服务已启动 (uvicorn app.main:app --reload)")
        return False
    
    # 步骤2：输入验证码
    print("\n[步骤2] 输入验证码...")
    sms_code = input("请输入收到的6位验证码: ").strip()
    
    if not sms_code or len(sms_code) != 6:
        print("❌ 验证码格式错误（应为6位数字）")
        return False
    
    # 步骤3：使用验证码登录
    print("\n[步骤3] 使用验证码登录...")
    try:
        response = requests.post(
            f"{BASE_URL}/users/login",
            json={
                "phone": phone,
                "sms_code": sms_code
            },
            headers={"X-Device-Type": "web"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            
            print("✅ 登录成功!")
            print(f"   Token: {access_token[:50]}...")
            
            # 步骤4：验证Token - 获取用户信息
            print("\n[步骤4] 验证Token - 获取用户信息...")
            response = requests.get(
                f"{BASE_URL}/users/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                print("✅ Token验证成功!")
                print(f"   用户ID: {user_data['id']}")
                print(f"   用户名: {user_data.get('username', 'N/A')}")
                print(f"   手机号: {user_data['phone']}")
                print(f"   角色: {user_data['role']}")
                return True
            else:
                print(f"❌ Token验证失败: {response.json()}")
                return False
                
        else:
            error = response.json()
            print(f"❌ 登录失败: {error.get('detail', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


def test_password_login():
    """测试密码登录（对比）"""
    
    phone = "18738710275"
    password = input("\n请输入密码（测试密码登录）: ").strip()
    
    if not password:
        print("跳过密码登录测试")
        return
    
    print("\n" + "="*70)
    print("🔑 密码登录测试")
    print("="*70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/users/login",
            json={
                "phone": phone,
                "password": password
            },
            headers={"X-Device-Type": "web"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ 密码登录成功!")
            print(f"   Token: {token_data['access_token'][:50]}...")
        else:
            error = response.json()
            print(f"❌ 密码登录失败: {error.get('detail', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")


if __name__ == "__main__":
    print("\n🔐 TimeKeeper - 短信验证码登录测试")
    print("="*70)
    print("测试手机号: 18738710275")
    print("前置条件: 该手机号已注册用户")
    print("="*70)
    
    # 测试短信验证码登录
    success = test_sms_login_flow()
    
    # 可选：测试密码登录
    if success:
        choice = input("\n是否测试密码登录？(y/n): ").strip().lower()
        if choice == 'y':
            test_password_login()
    
    print("\n" + "="*70)
    if success:
        print("✅ 测试完成: 短信验证码登录成功")
    else:
        print("❌ 测试完成: 短信验证码登录失败")
    print("="*70)
