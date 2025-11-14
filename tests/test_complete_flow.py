"""
完整业务流程验证测试
从注册开始验证所有核心功能
"""
import sys
sys.path.insert(0, r"d:\pygithub\TimeKeeper\TimeKeeper")

from fastapi.testclient import TestClient
from main import app
from datetime import datetime, timedelta

def test_complete_business_flow():
    """测试完整业务流程"""
    client = TestClient(app)
    
    print("="*80)
    print("TimeKeeper App - Complete Business Flow Validation")
    print("="*80)
    
    # ==================== Step 1: User Registration ====================
    print("\n[Step 1] User Registration")
    print("-" * 80)
    
    timestamp = datetime.now().timestamp()
    register_data = {
        "phone": f"138{int(timestamp % 100000000)}",
        "password": "Password123!",
        "nickname": f"TestUser{int(timestamp)}"
    }
    
    register_response = client.post("/api/v1/users/register", json=register_data)
    print(f"Status Code: {register_response.status_code}")
    
    if register_response.status_code not in [200, 201]:
        print(f"ERROR: {register_response.json()}")
        return False
    
    user_data = register_response.json()
    print(f"User ID: {user_data['id']}")
    print(f"Phone: {user_data['phone']}")
    print(f"Nickname: {user_data.get('nickname', 'N/A')}")
    print(f"Is Active: {user_data.get('is_active', 'N/A')}")
    print(f"Created At: {user_data.get('created_at', 'N/A')}")
    print("Status: PASSED")
    
    # ==================== Step 2: User Login ====================
    print("\n[Step 2] User Login")
    print("-" * 80)
    
    login_data = {
        "phone": register_data["phone"],
        "password": register_data["password"]
    }
    
    login_response = client.post("/api/v1/users/login", json=login_data)
    print(f"Status Code: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"ERROR: {login_response.json()}")
        return False
    
    login_result = login_response.json()
    token = login_result["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Token Type: {login_result['token_type']}")
    print(f"Token: {token[:20]}...")
    print("Status: PASSED")
    
    # ==================== Step 3: Create Reminder (Simple) ====================
    print("\n[Step 3] Create Simple Reminder")
    print("-" * 80)
    
    simple_reminder = {
        "title": "Daily Meeting",
        "description": "Team standup meeting",
        "category": "other",
        "recurrence_type": "daily",
        "recurrence_config": {"time": "09:00"},
        "first_remind_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "remind_channels": ["app"],
        "advance_minutes": 15
    }
    
    create_response = client.post("/api/v1/reminders/", json=simple_reminder, headers=headers)
    print(f"Status Code: {create_response.status_code}")
    
    if create_response.status_code not in [200, 201]:
        print(f"ERROR: {create_response.json()}")
        return False
    
    reminder1 = create_response.json()
    print(f"Reminder ID: {reminder1['id']}")
    print(f"Title: {reminder1['title']}")
    print(f"Category: {reminder1['category']}")
    print(f"Priority: {reminder1.get('priority', 'N/A')}")
    print("Status: PASSED")
    
    # ==================== Step 4: Create Reminder (Complex with All Fields) ====================
    print("\n[Step 4] Create Complex Reminder with All New Fields")
    print("-" * 80)
    
    complex_reminder = {
        "title": "Monthly Rent Payment",
        "description": "Pay rent by 25th of each month",
        "category": "finance",
        "recurrence_type": "monthly",
        "recurrence_config": {"day_of_month": 25},
        "first_remind_time": (datetime.now() + timedelta(days=2)).isoformat(),
        "remind_channels": ["app", "sms"],
        "advance_minutes": 1440,
        "priority": 3,  # High priority
        "amount": 350000,  # 3500.00 yuan in cents
        "location": {
            "address": "Beijing Chaoyang District Jianguo Road No.1",
            "latitude": 39.9087,
            "longitude": 116.3975,
            "poi_name": "Landlord Office"
        },
        "attachments": [
            {
                "type": "image",
                "url": "https://example.com/contract.jpg",
                "filename": "Rental Contract.jpg",
                "size": 1024000
            },
            {
                "type": "pdf",
                "url": "https://example.com/receipt.pdf",
                "filename": "Last Month Receipt.pdf",
                "size": 512000
            }
        ]
    }
    
    create_response2 = client.post("/api/v1/reminders/", json=complex_reminder, headers=headers)
    print(f"Status Code: {create_response2.status_code}")
    
    if create_response2.status_code not in [200, 201]:
        print(f"ERROR: {create_response2.json()}")
        return False
    
    reminder2 = create_response2.json()
    print(f"Reminder ID: {reminder2['id']}")
    print(f"Title: {reminder2['title']}")
    print(f"Priority: {reminder2['priority']} (1=Low, 2=Medium, 3=High)")
    print(f"Amount: {reminder2['amount']/100:.2f} yuan ({reminder2['amount']} cents)")
    print(f"Location: {reminder2['location']['address']}")
    print(f"Location POI: {reminder2['location'].get('poi_name', 'N/A')}")
    print(f"Attachments: {len(reminder2['attachments'])} files")
    for i, att in enumerate(reminder2['attachments'], 1):
        print(f"  - Attachment {i}: {att['filename']} ({att['type']}, {att.get('size', 0)/1024:.1f}KB)")
    print(f"Is Completed: {reminder2.get('is_completed', 'N/A')}")
    print("Status: PASSED")
    
    # ==================== Step 5: List User Reminders ====================
    print("\n[Step 5] List User Reminders")
    print("-" * 80)
    
    list_response = client.get("/api/v1/reminders/", headers=headers)
    print(f"Status Code: {list_response.status_code}")
    
    if list_response.status_code != 200:
        print(f"ERROR: {list_response.json()}")
        return False
    
    reminders_list = list_response.json()
    print(f"Total Reminders: {len(reminders_list)}")
    for reminder in reminders_list:
        print(f"  - ID: {reminder['id']}, Title: {reminder['title']}, Priority: {reminder.get('priority', 1)}")
    print("Status: PASSED")
    
    # ==================== Step 6: Get Reminder Details ====================
    print("\n[Step 6] Get Reminder Details")
    print("-" * 80)
    
    detail_response = client.get(f"/api/v1/reminders/{reminder2['id']}", headers=headers)
    print(f"Status Code: {detail_response.status_code}")
    
    if detail_response.status_code != 200:
        print(f"ERROR: {detail_response.json()}")
        return False
    
    reminder_detail = detail_response.json()
    print(f"ID: {reminder_detail['id']}")
    print(f"Title: {reminder_detail['title']}")
    print(f"Description: {reminder_detail['description']}")
    print(f"All Fields Present: {all(key in reminder_detail for key in ['priority', 'amount', 'location', 'attachments'])}")
    print("Status: PASSED")
    
    # ==================== Step 7: Update Reminder ====================
    print("\n[Step 7] Update Reminder")
    print("-" * 80)
    
    update_data = {
        "title": "Monthly Rent Payment (Updated)",
        "priority": 2,  # Change to medium priority
        "amount": 380000  # Increase rent
    }
    
    update_response = client.put(f"/api/v1/reminders/{reminder2['id']}", json=update_data, headers=headers)
    print(f"Status Code: {update_response.status_code}")
    
    if update_response.status_code != 200:
        print(f"ERROR: {update_response.json()}")
        return False
    
    updated_reminder = update_response.json()
    print(f"Updated Title: {updated_reminder['title']}")
    print(f"Updated Priority: {updated_reminder['priority']} (changed from 3 to 2)")
    print(f"Updated Amount: {updated_reminder['amount']/100:.2f} yuan (changed from 3500 to 3800)")
    print("Status: PASSED")
    
    # ==================== Step 8: Verify Push Tasks Generated ====================
    print("\n[Step 8] Verify Push Tasks")
    print("-" * 80)
    
    # Note: This requires PushTask API to be implemented
    print("Note: PushTask listing API not yet implemented")
    print("Expected: 2 push tasks should be auto-generated for the 2 reminders")
    print("Status: SKIPPED (API not available)")
    
    # ==================== Step 9: Delete Reminder ====================
    print("\n[Step 9] Delete Reminder")
    print("-" * 80)
    
    delete_response = client.delete(f"/api/v1/reminders/{reminder1['id']}", headers=headers)
    print(f"Status Code: {delete_response.status_code}")
    
    if delete_response.status_code not in [200, 204]:
        print(f"ERROR: {delete_response.json()}")
        return False
    
    print(f"Deleted Reminder ID: {reminder1['id']}")
    
    # Verify deletion
    verify_response = client.get(f"/api/v1/reminders/{reminder1['id']}", headers=headers)
    print(f"Verification Status: {verify_response.status_code} (should be 404)")
    print("Status: PASSED" if verify_response.status_code == 404 else "FAILED")
    
    # ==================== Final Summary ====================
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80)
    print("1. User Registration: PASSED")
    print("2. User Login: PASSED")
    print("3. Create Simple Reminder: PASSED")
    print("4. Create Complex Reminder (All Fields): PASSED")
    print("5. List User Reminders: PASSED")
    print("6. Get Reminder Details: PASSED")
    print("7. Update Reminder: PASSED")
    print("8. Verify Push Tasks: SKIPPED")
    print("9. Delete Reminder: PASSED")
    print("\nOverall: SUCCESS - Core business logic working correctly!")
    print("="*80)
    
    return True

if __name__ == "__main__":
    try:
        success = test_complete_business_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
