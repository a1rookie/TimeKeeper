"""
Database Initialization Script
数据库初始化脚本 - 自动创建数据库
"""

import sys
import os
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def create_database():
    """Create TimeKeeper database if it doesn't exist"""
    
    print("=" * 60)
    print("🗄️  TimeKeeper Database Initialization")
    print("=" * 60)
    
    # Parse DATABASE_URL from environment or use defaults
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:Admin%40123@localhost:5432/timekeeper')
    parsed = urlparse(database_url)
    
    # Database connection parameters
    db_params = {
        'host': '127.0.0.1',  # Use IPv4 explicitly instead of localhost
        'port': parsed.port or 5432,
        'user': parsed.username or 'postgres',
        'password': unquote(parsed.password) if parsed.password else 'postgres'  # URL decode password
    }
    
    db_name = parsed.path.lstrip('/') or 'timekeeper'
    
    try:
        # Connect to PostgreSQL server (not to a specific database)
        print("\n📡 Connecting to PostgreSQL server...")
        print(f"   Host: {db_params['host']}:{db_params['port']}")
        print(f"   User: {db_params['user']}")
        print(f"   Password parsed: {db_params['password'][:5]}... (length: {len(db_params['password'])})")  # Debug
        
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Connected to PostgreSQL server")
        
        # Check if database exists
        print(f"\n🔍 Checking if database '{db_name}' exists...")
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        
        exists = cursor.fetchone()
        
        if exists:
            print(f"⚠️  Database '{db_name}' already exists")
            response = input("\n   Do you want to recreate it? (yes/no): ").lower()
            
            if response == 'yes':
                print(f"\n🗑️  Dropping database '{db_name}'...")
                cursor.execute(f"DROP DATABASE {db_name}")
                print(f"✅ Database '{db_name}' dropped")
                exists = False
            else:
                print("\n✅ Using existing database")
                cursor.close()
                conn.close()
                return True
        
        if not exists:
            # Create database
            print(f"\n🏗️  Creating database '{db_name}'...")
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"✅ Database '{db_name}' created successfully!")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Database initialization completed!")
        print("\n📝 Next steps:")
        print("   1. Update .env file with your database credentials")
        print("   2. Run: alembic revision --autogenerate -m 'Initial'")
        print("   3. Run: alembic upgrade head")
        print("=" * 60)
        
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure PostgreSQL is running")
        print("   2. Check username and password in this script")
        print("   3. Check PostgreSQL is listening on port 5432")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def main():
    """Main function"""
    if create_database():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
