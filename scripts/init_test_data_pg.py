"""
初始化PostgreSQL测试数据
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.user import User
from app.models.reminder import Reminder, RecurrenceType, ReminderCategory
from app.core.security import get_password_hash
from datetime import datetime

def init_test_data():
    """Initialize test data in PostgreSQL"""
    
    print("="*60)
    print("Initializing PostgreSQL Test Data")
    print("="*60)
    
    with Session(engine) as db:
        # Check if test user exists
        existing_user = db.query(User).filter(User.phone == "13800138000").first()
        
        if existing_user:
            print("\n[INFO] Test user already exists")
            user_id = existing_user.id
        else:
            # Create test user
            print("\n[1] Creating test user...")
            test_user = User(
                phone="13800138000",
                hashed_password=get_password_hash("test123"),
                nickname="Test User"
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            user_id = test_user.id
            print(f"    [OK] Created user ID: {user_id}")
        
        # Create test reminder
        print("\n[2] Creating test reminder...")
        test_reminder = Reminder(
            user_id=user_id,
            title="测试提醒 - 交房租",
            description="每月1号提醒交房租",
            category=ReminderCategory.RENT,
            recurrence_type=RecurrenceType.MONTHLY,
            recurrence_config={"day_of_month": 1},
            first_remind_time=datetime(2025, 1, 1, 9, 0),
            next_remind_time=datetime(2025, 12, 1, 9, 0),
            remind_channels=["app"],
            advance_minutes=0,
            is_active=True
        )
        db.add(test_reminder)
        db.commit()
        db.refresh(test_reminder)
        print(f"    [OK] Created reminder ID: {test_reminder.id}")
        
        # Verify
        print("\n[3] Verifying data...")
        user_count = db.query(User).count()
        reminder_count = db.query(Reminder).count()
        print(f"    [OK] Users: {user_count}, Reminders: {reminder_count}")
        
    print("\n" + "="*60)
    print("[SUCCESS] PostgreSQL test data initialized!")
    print("="*60)
    print("\nTest credentials:")
    print("  Phone: 13800138000")
    print("  Password: test123")
    print("\nReady to test with: python test_final.py")

if __name__ == "__main__":
    init_test_data()
