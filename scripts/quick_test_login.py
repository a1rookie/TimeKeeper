"""
快速测试短信验证码登录 - 手动输入验证码
"""
import requests

BASE_URL = "http://localhost:8000/api/v1"
PHONE = "18738710275"

def test_sms_login():
    print("\n" + "="*70)
    print("📱 短信验证码登录快速测试")
    print("="*70)
    
    # 1. 发送验证码
    print(f"\n[步骤1] 发送登录验证码到 {PHONE}...")
    try:
        response = requests.post(
            f"{BASE_URL}/users/send-sms-code",
            json={
                "phone": PHONE,
                "purpose": "login"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 验证码已发送")
            print(f"   有效期: {data['data']['expires_in']} 秒")
        else:
            print(f"❌ 发送失败: {response.status_code}")
            print(f"   详情: {response.json()}")
            return
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        print("   提示: 请确保 FastAPI 服务已启动")
        print("   启动命令: uvicorn main:app --reload --port 8000")
        return
    
    # 2. 输入验证码
    print("\n[步骤2] 请查收手机短信...")
    sms_code = input("请输入收到的验证码: ").strip()
    
    if not sms_code:
        print("❌ 验证码不能为空")
        return
    
    # 3. 使用验证码登录
    print("\n[步骤3] 使用验证码登录...")
    try:
        response = requests.post(
            f"{BASE_URL}/users/login",
            json={
                "phone": PHONE,
                "sms_code": sms_code
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ 登录成功!")
            print(f"   Token类型: {data['token_type']}")
            print(f"   访问令牌: {data['access_token'][:50]}...")
            print("   用户信息:")
            print(f"   - ID: {data['user']['id']}")
            print(f"   - 手机号: {data['user']['phone']}")
            print(f"   - 昵称: {data['user']['nickname']}")
            print(f"   - 角色: {data['user']['role']}")
        else:
            print(f"❌ 登录失败: {response.status_code}")
            print(f"   详情: {response.json()}")
            
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    print("🔐 TimeKeeper - 短信验证码登录测试")
    print(f"测试手机号: {PHONE}")
    test_sms_login()
