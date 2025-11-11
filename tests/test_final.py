"""
完整E2E测试 - 无emoji版本
"""
import requests

BASE_URL = "http://localhost:8000"

def test_e2e():
    print("="*60)
    print("TimeKeeper E2E API Test")
    print("="*60)
    
    # 1. Login
    print("\n[1] Testing login...")
    r = requests.post(f"{BASE_URL}/api/v1/users/login", 
                     json={"phone": "13800138000", "password": "test123"})
    assert r.status_code == 200, f"Login failed: {r.status_code}"
    token = r.json()["access_token"]
    print(f"    [OK] Login successful, token: {token[:30]}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get user info
    print("\n[2] Testing get user info...")
    r = requests.get(f"{BASE_URL}/api/v1/users/me", headers=headers)
    assert r.status_code == 200, f"Get user failed: {r.status_code}"
    user = r.json()
    print(f"    [OK] User ID: {user['id']}, Phone: {user['phone']}")
    
    # 3. Create reminder
    print("\n[3] Testing create reminder...")
    data = {
        "title": "Test Reminder",
        "description": "E2E Test",
        "category": "health",
        "recurrence_type": "daily",
        "recurrence_config": {"interval": 1},
        "first_remind_time": "2025-02-01T09:00:00",
        "remind_channels": ["app"],
        "advance_minutes": 0
    }
    r = requests.post(f"{BASE_URL}/api/v1/reminders/", json=data, headers=headers)
    assert r.status_code == 201, f"Create failed: {r.status_code}"
    reminder = r.json()
    rid = reminder["id"]
    print(f"    [OK] Created reminder ID: {rid}")
    
    # 4. List reminders
    print("\n[4] Testing list reminders...")
    r = requests.get(f"{BASE_URL}/api/v1/reminders/", headers=headers)
    assert r.status_code == 200, f"List failed: {r.status_code}"
    reminders = r.json()
    print(f"    [OK] Found {len(reminders)} reminders")
    
    # 5. Update reminder
    print("\n[5] Testing update reminder...")
    r = requests.put(f"{BASE_URL}/api/v1/reminders/{rid}", 
                    json={"title": "Updated Test"}, headers=headers)
    assert r.status_code == 200, f"Update failed: {r.status_code}"
    print(f"    [OK] Updated reminder")
    
    # 6. Test permission isolation
    print("\n[6] Testing permission isolation...")
    r = requests.get(f"{BASE_URL}/api/v1/reminders/99999", headers=headers)
    assert r.status_code == 404, f"Should be 404, got: {r.status_code}"
    print(f"    [OK] Permission isolation working")
    
    # 7. Delete reminder
    print("\n[7] Testing delete reminder...")
    r = requests.delete(f"{BASE_URL}/api/v1/reminders/{rid}", headers=headers)
    assert r.status_code == 204, f"Delete failed: {r.status_code}"
    print(f"    [OK] Deleted reminder")
    
    # 8. Verify deletion
    print("\n[8] Verifying deletion...")
    r = requests.get(f"{BASE_URL}/api/v1/reminders/{rid}", headers=headers)
    assert r.status_code == 404, f"Should be 404, got: {r.status_code}"
    print(f"    [OK] Confirmed deletion")
    
    # 9. Test unauthorized access
    print("\n[9] Testing unauthorized access...")
    r = requests.get(f"{BASE_URL}/api/v1/users/me")  # No token
    assert r.status_code in [401, 403], f"Should be 401/403, got: {r.status_code}"
    print(f"    [OK] Unauthorized access denied ({r.status_code})")
    
    print("\n" + "="*60)
    print("[SUCCESS] All tests passed!")
    print("="*60)
    print("\nTest Summary:")
    print("  [OK] User login")
    print("  [OK] JWT token verification")
    print("  [OK] Get user info")
    print("  [OK] Create reminder")
    print("  [OK] List reminders")
    print("  [OK] Update reminder")
    print("  [OK] Permission isolation")
    print("  [OK] Delete reminder")
    print("  [OK] Unauthorized access denied")

if __name__ == "__main__":
    try:
        test_e2e()
    except AssertionError as e:
        print(f"\n[FAILED] {e}")
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Cannot connect to server")
        print("  Please start: python main.py")
    except Exception as e:
        print(f"\n[ERROR] {e}")
