"""
Database Verification Script
数据库验证脚本 - 检查数据库结构和连接
"""

import sys
from sqlalchemy import create_engine, inspect, text
from app.core.config import settings

def verify_database():
    """Verify database connection and structure"""
    
    print("=" * 60)
    print("🔍 TimeKeeper Database Verification")
    print("=" * 60)
    
    try:
        # Test database connection
        print("\n📡 Testing database connection...")
        print(f"   URL: {settings.DATABASE_URL.replace('password', '***')}")
        
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL")
            print(f"   Version: {version[:50]}...")
        
        # Check tables
        print("\n📋 Checking tables...")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = ['users', 'reminders', 'push_tasks', 'alembic_version']
        
        for table in expected_tables:
            if table in tables:
                print(f"   ✅ {table}")
                
                # Show column count
                columns = inspector.get_columns(table)
                print(f"      Columns: {len(columns)}")
                
                # Show indexes
                if table != 'alembic_version':
                    indexes = inspector.get_indexes(table)
                    if indexes:
                        print(f"      Indexes: {len(indexes)}")
            else:
                print(f"   ❌ {table} - NOT FOUND")
        
        # Check foreign keys
        print("\n🔗 Checking foreign keys...")
        
        reminder_fks = inspector.get_foreign_keys('reminders')
        if reminder_fks:
            print(f"   ✅ reminders has {len(reminder_fks)} foreign key(s)")
            for fk in reminder_fks:
                print(f"      → {fk['referred_table']}")
        
        push_task_fks = inspector.get_foreign_keys('push_tasks')
        if push_task_fks:
            print(f"   ✅ push_tasks has {len(push_task_fks)} foreign key(s)")
            for fk in push_task_fks:
                print(f"      → {fk['referred_table']}")
        
        # Check alembic version
        print("\n📦 Checking migration version...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.fetchone()
            if version:
                print(f"   ✅ Current version: {version[0]}")
            else:
                print("   ⚠️  No migration version found")
        
        # Test data operations
        print("\n🧪 Testing basic operations...")
        from app.models.user import User
        from app.core.database import Base, SessionLocal
        
        # Create tables if not exists (just in case)
        Base.metadata.create_all(bind=engine)
        
        # Test insert
        db = SessionLocal()
        try:
            # Check if test user exists
            test_user = db.query(User).filter(User.phone == "00000000000").first()
            if test_user:
                print("   ℹ️  Test user already exists, skipping...")
            else:
                print("   Testing INSERT...")
                from app.core.security import get_password_hash
                
                test_user = User(
                    phone="00000000000",
                    nickname="test_verification",
                    hashed_password=get_password_hash("test123")
                )
                db.add(test_user)
                db.commit()
                print("   ✅ INSERT successful")
                
                # Test select
                print("   Testing SELECT...")
                user = db.query(User).filter(User.phone == "00000000000").first()
                assert user is not None
                print(f"   ✅ SELECT successful (ID: {user.id})")
                
                # Test update
                print("   Testing UPDATE...")
                user.nickname = "test_updated"
                db.commit()
                print("   ✅ UPDATE successful")
                
                # Test delete
                print("   Testing DELETE...")
                db.delete(user)
                db.commit()
                print("   ✅ DELETE successful")
                
        finally:
            db.close()
        
        print("\n" + "=" * 60)
        print("✅ Database verification completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Start the application: python main.py")
        print("   2. Visit API docs: http://localhost:8000/docs")
        print("   3. Test user registration and login")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check if database exists")
        print("   2. Run migrations: alembic upgrade head")
        print("   3. Check DATABASE_URL in .env file")
        return False


def main():
    """Main function"""
    if verify_database():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
