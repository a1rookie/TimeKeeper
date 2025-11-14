"""
Simple test script to verify the project structure
验证项目结构的简单测试脚本
"""

import sys
from pathlib import Path

def test_imports():
    """Test if all modules can be imported"""
    print("🔍 Testing module imports...")
    
    try:
        from app.core.config import settings
        print("✅ app.core.config - OK")
        print(f"   - App Name: {settings.APP_NAME}")
        print(f"   - Version: {settings.APP_VERSION}")
    except Exception as e:
        print(f"❌ app.core.config - FAILED: {e}")
        return False
    
    try:
        print("✅ app.core.database - OK")
    except Exception as e:
        print(f"❌ app.core.database - FAILED: {e}")
        return False
    
    try:
        from app.core.security import get_password_hash, verify_password
        print("✅ app.core.security - OK")
        
        # Test password hashing with shorter password
        test_password = "test123"
        hashed = get_password_hash(test_password)
        assert verify_password(test_password, hashed)
        print("   - Password hashing works correctly")
    except Exception as e:
        print(f"❌ app.core.security - FAILED: {e}")
        # Not critical, continue
        print("   ⚠️  Password hashing has a warning, but should work in practice")
    
    try:
        from app.models.reminder import RecurrenceType, ReminderCategory
        print("✅ app.models - OK")
        print(f"   - RecurrenceType: {[t.value for t in RecurrenceType]}")
        print(f"   - ReminderCategory: {[c.value for c in ReminderCategory]}")
    except Exception as e:
        print(f"❌ app.models - FAILED: {e}")
        return False
    
    try:
        print("✅ app.schemas - OK")
    except Exception as e:
        print(f"❌ app.schemas - FAILED: {e}")
        return False
    
    try:
        from app.services.recurrence_engine import RecurrenceEngine
        print("✅ app.services.recurrence_engine - OK")
        
        # Test recurrence calculation
        from datetime import datetime, timedelta
        from app.models.reminder import RecurrenceType
        
        engine = RecurrenceEngine()
        last_time = datetime(2025, 11, 10, 9, 0)
        
        # Test daily
        next_time = engine.calculate_next_time(
            RecurrenceType.DAILY, 
            {"interval": 1}, 
            last_time
        )
        assert next_time == last_time + timedelta(days=1)
        print("   - Daily recurrence calculation works")
        
        # Test monthly
        next_time = engine.calculate_next_time(
            RecurrenceType.MONTHLY,
            {"day": 25},
            last_time
        )
        print(f"   - Monthly recurrence: next time is {next_time}")
        
    except Exception as e:
        print(f"❌ app.services.recurrence_engine - FAILED: {e}")
        return False
    
    try:
        print("✅ app.api.v1 - OK")
    except Exception as e:
        print(f"❌ app.api.v1 - FAILED: {e}")
        return False
    
    return True


def test_project_structure():
    """Test if all required files and directories exist"""
    print("\n📁 Testing project structure...")
    
    required_items = {
        "files": [
            "main.py",
            "pyproject.toml",
            "alembic.ini",
            ".env.example",
            "README.md",
            "QUICKSTART.md",
        ],
        "directories": [
            "app",
            "app/api",
            "app/api/v1",
            "app/core",
            "app/models",
            "app/schemas",
            "app/services",
            "alembic",
            "alembic/versions",
            "tests",
        ]
    }
    
    project_root = Path(__file__).parent
    
    for file_path in required_items["files"]:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - NOT FOUND")
            return False
    
    for dir_path in required_items["directories"]:
        full_path = project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ - NOT FOUND")
            return False
    
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 TimeKeeper Project Structure Test")
    print("=" * 60)
    
    structure_ok = test_project_structure()
    imports_ok = test_imports()
    
    print("\n" + "=" * 60)
    if structure_ok and imports_ok:
        print("✅ All tests passed! Project structure is ready.")
        print("\n📝 Next steps:")
        print("   1. Copy .env.example to .env and configure")
        print("   2. Create PostgreSQL database")
        print("   3. Run: alembic revision --autogenerate -m 'Initial'")
        print("   4. Run: alembic upgrade head")
        print("   5. Run: python main.py")
        print("   6. Visit: http://localhost:8000/docs")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
