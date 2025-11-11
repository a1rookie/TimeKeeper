"""
Local Development Database Setup
本地开发数据库设置 - 使用 SQLite
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.database import Base
from app.models.user import User
from app.models.reminder import Reminder
from app.models.push_task import PushTask

def setup_sqlite_dev_db():
    """Setup SQLite database for local development"""
    
    print("=" * 60)
    print("🗄️  Local Development Database Setup (SQLite)")
    print("=" * 60)
    
    try:
        # Create database file path
        db_path = Path("timekeeper_dev.db")
        
        if db_path.exists():
            print(f"\n⚠️  Database file '{db_path}' already exists")
            response = input("   Delete and recreate? (yes/no): ").lower()
            if response == 'yes':
                db_path.unlink()
                print(f"   🗑️  Deleted {db_path}")
            else:
                print("   ℹ️  Using existing database")
        
        # Create engine
        database_url = f"sqlite:///./{db_path}"
        print(f"\n📡 Creating SQLite database...")
        print(f"   Path: {db_path.absolute()}")
        
        engine = create_engine(database_url, echo=False)
        
        # Create all tables
        print("\n🏗️  Creating tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify tables
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            tables = [row[0] for row in result]
            
            print("\n📋 Created tables:")
            for table in tables:
                if table != 'sqlite_sequence':
                    print(f"   ✅ {table}")
        
        # Test operations
        print("\n🧪 Testing database operations...")
        from sqlalchemy.orm import sessionmaker
        from app.core.security import get_password_hash
        
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            # Insert test user
            test_user = User(
                phone="13800138000",
                nickname="测试用户",
                hashed_password=get_password_hash("test123")
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"   ✅ Created test user (ID: {test_user.id})")
            
            # Insert test reminder
            from datetime import datetime, timedelta
            from app.models.reminder import RecurrenceType, ReminderCategory
            
            test_reminder = Reminder(
                user_id=test_user.id,
                title="测试提醒 - 交房租",
                description="每月25号提醒交房租",
                category=ReminderCategory.RENT,
                recurrence_type=RecurrenceType.MONTHLY,
                recurrence_config={"day": 25},
                first_remind_time=datetime.now() + timedelta(days=1),
                next_remind_time=datetime.now() + timedelta(days=1)
            )
            db.add(test_reminder)
            db.commit()
            db.refresh(test_reminder)
            print(f"   ✅ Created test reminder (ID: {test_reminder.id})")
            
            # Query test
            user = db.query(User).filter(User.phone == "13800138000").first()
            reminders = db.query(Reminder).filter(Reminder.user_id == user.id).all()
            print(f"   ✅ Query test passed ({len(reminders)} reminders)")
            
        finally:
            db.close()
        
        print("\n" + "=" * 60)
        print("✅ SQLite database setup completed!")
        print(f"\n📝 Database file: {db_path.absolute()}")
        print("\n⚙️  To use this database:")
        print("   1. Update .env file:")
        print(f"      DATABASE_URL=sqlite:///./{db_path}")
        print("   2. Start server: python main.py")
        print("   3. Test login:")
        print("      Phone: 13800138000")
        print("      Password: test123")
        print("\n💡 For production, use PostgreSQL")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("\n💡 This script creates a SQLite database for local development")
    print("   No PostgreSQL installation required!\n")
    
    if setup_sqlite_dev_db():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
