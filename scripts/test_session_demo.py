"""
Simple Session Management Demo
用已存在用户演示会话管理功能
"""
import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"

# 使用数据库中真实存在的用户
PHONE = "13800138000"
PASSWORD = "password123"  # 需要知道密码，或先注册新用户

print("="*70)
print("Session Management Demo")
print("="*70)

# 步骤1: 先尝试注册新用户（如果失败说明用户已存在）
print("\n[Step 1] Register new user...")
new_phone = "13666666666"  # Change phone to avoid conflict
new_password = "password123"

r = requests.post(
    f"{BASE_URL}/users/register",
    json={
        "phone": new_phone,
        "password": new_password,
        "nickname": "SessionTestUser"
    }
)

if r.status_code == 201:
    print(f"   OK - User registered: {new_phone}")
    PHONE = new_phone
    PASSWORD = new_password
elif "已存在" in r.text or "exists" in r.text.lower():
    print(f"   INFO - User already exists, will use existing user")
    PHONE = new_phone
    PASSWORD = new_password
else:
    print(f"   WARN - Register failed ({r.status_code}), will try login with existing user")

# 步骤2: 第一次从Web登录
print(f"\n[Step 2] Login from WEB (1st time)...")
r1 = requests.post(
    f"{BASE_URL}/users/login",
    json={"phone": PHONE, "password": PASSWORD},
    headers={"X-Device-Type": "web"}
)

if r1.status_code != 200:
    print(f"   FAIL - Status {r1.status_code}: {r1.text[:200]}")
    print("\n[ERROR] Cannot proceed without valid credentials")
    sys.exit(1)

token1 = r1.json()["access_token"]
print(f"   OK - Token1: ...{token1[-20:]}")

# 步骤3: 验证token1有效
print(f"\n[Step 3] Verify token1...")
r = requests.get(
    f"{BASE_URL}/users/me",
    headers={"Authorization": f"Bearer {token1}"}
)
print(f"   {'OK' if r.status_code==200 else 'FAIL'} - Token1 is {'valid' if r.status_code==200 else 'invalid'}")

# 步骤4: 第二次从Web登录（应该踢掉token1）
print(f"\n[Step 4] Login from WEB (2nd time) - should kick token1...")
r2 = requests.post(
    f"{BASE_URL}/users/login",
    json={"phone": PHONE, "password": PASSWORD},
    headers={"X-Device-Type": "web"}
)

if r2.status_code != 200:
    print(f"   FAIL - Status {r2.status_code}")
else:
    token2 = r2.json()["access_token"]
    print(f"   OK - Token2: ...{token2[-20:]}")

# 步骤5: 验证token1被踢掉
print(f"\n[Step 5] Verify token1 is kicked...")
r = requests.get(
    f"{BASE_URL}/users/me",
    headers={"Authorization": f"Bearer {token1}"}
)
if r.status_code == 401:
    print(f"   SUCCESS! Token1 was kicked (401: {r.json().get('detail', '')})")
else:
    print(f"   FAIL - Token1 still valid (status {r.status_code})")

# 步骤6: 验证token2有效
print(f"\n[Step 6] Verify token2 is valid...")
r = requests.get(
    f"{BASE_URL}/users/me",
    headers={"Authorization": f"Bearer {token2}"}
)
if r.status_code == 200:
    print(f"   SUCCESS! Token2 is valid (user: {r.json()['phone']})")
else:
    print(f"   FAIL - Token2 invalid (status {r.status_code})")

# 步骤7: 从iOS登录（不应该踢掉Web token2）
print(f"\n[Step 7] Login from iOS (different device type)...")
r3 = requests.post(
    f"{BASE_URL}/users/login",
    json={"phone": PHONE, "password": PASSWORD},
    headers={"X-Device-Type": "ios"}
)

if r3.status_code != 200:
    print(f"   FAIL - Status {r3.status_code}")
else:
    token_ios = r3.json()["access_token"]
    print(f"   OK - iOS Token: ...{token_ios[-20:]}")

# 步骤8: 验证Web token2仍然有效
print(f"\n[Step 8] Verify Web token2 still valid...")
r = requests.get(
    f"{BASE_URL}/users/me",
    headers={"Authorization": f"Bearer {token2}"}
)
if r.status_code == 200:
    print(f"   SUCCESS! Web token2 still valid (multi-device works)")
else:
    print(f"   FAIL - Web token2 was kicked (should not happen)")

# 步骤9: 查询所有活跃会话
print(f"\n[Step 9] Query all active sessions...")
r = requests.get(
    f"{BASE_URL}/users/sessions",
    headers={"Authorization": f"Bearer {token2}"}
)
if r.status_code == 200:
    sessions = r.json()
    print(f"   OK - {len(sessions)} active sessions:")
    for device, info in sessions.items():
        if isinstance(info, dict):
            print(f"      - {device}: {info.get('expires_in_seconds', 'N/A')}s left")
        else:
            print(f"      - {device}: {info}s left")
else:
    print(f"   FAIL - Status {r.status_code}")

print("\n" + "="*70)
print("Demo completed!")
print("="*70)
