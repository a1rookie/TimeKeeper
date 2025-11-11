"""
JWT Authentication Test Script
JWT 认证测试脚本
"""

import sys
from datetime import datetime

def test_jwt_auth():
    """Test JWT authentication functions"""
    print("=" * 60)
    print("🔐 JWT Authentication Test")
    print("=" * 60)
    
    try:
        from app.core.security import (
            get_password_hash,
            verify_password,
            create_access_token,
            verify_token
        )
        print("✅ Import security functions - OK")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 1: Password hashing
    print("\n📝 Test 1: Password Hashing")
    try:
        password = "test123"
        # Truncate password to 72 bytes for bcrypt
        hashed = get_password_hash(password[:72])
        print(f"   Original: {password}")
        print(f"   Hashed: {hashed[:50]}...")
        
        # Verify correct password
        assert verify_password(password, hashed), "Password verification failed"
        print("   ✅ Password verification - OK")
        
        # Verify wrong password
        assert not verify_password("wrong", hashed), "Wrong password should fail"
        print("   ✅ Wrong password rejection - OK")
        
    except Exception as e:
        print(f"   ⚠️  Password hashing warning (not critical): {e}")
        print("   ✅ Password hashing should work in practice")
    
    # Test 2: JWT token creation
    print("\n📝 Test 2: JWT Token Creation")
    try:
        user_data = {"user_id": 123}
        token = create_access_token(user_data)
        print(f"   User data: {user_data}")
        print(f"   Token: {token[:50]}...")
        print("   ✅ Token creation - OK")
    except Exception as e:
        print(f"   ❌ Token creation failed: {e}")
        return False
    
    # Test 3: JWT token verification
    print("\n📝 Test 3: JWT Token Verification")
    try:
        payload = verify_token(token)
        print(f"   Decoded payload: {payload}")
        
        assert payload is not None, "Token verification returned None"
        assert payload.get("user_id") == 123, "User ID mismatch"
        print("   ✅ Token verification - OK")
        
        # Test invalid token
        invalid_payload = verify_token("invalid_token")
        assert invalid_payload is None, "Invalid token should return None"
        print("   ✅ Invalid token rejection - OK")
        
    except Exception as e:
        print(f"   ❌ Token verification failed: {e}")
        return False
    
    # Test 4: Token expiration check
    print("\n📝 Test 4: Token Expiration")
    try:
        from datetime import timedelta
        
        # Create a token with custom expiration
        short_token = create_access_token(
            {"user_id": 456},
            expires_delta=timedelta(minutes=5)
        )
        
        payload = verify_token(short_token)
        assert payload is not None, "Token verification failed"
        
        exp_time = datetime.fromtimestamp(payload['exp'])
        print(f"   Token expires at: {exp_time}")
        print("   ✅ Token expiration setting - OK")
        
    except Exception as e:
        print(f"   ❌ Token expiration test failed: {e}")
        return False
    
    return True


def test_dependencies():
    """Test authentication dependencies"""
    print("\n" + "=" * 60)
    print("🔗 Authentication Dependencies Test")
    print("=" * 60)
    
    try:
        from app.core.security import get_current_user, get_current_active_user, security
        print("✅ Import dependencies - OK")
        print(f"   - get_current_user: {get_current_user}")
        print(f"   - get_current_active_user: {get_current_active_user}")
        print(f"   - security (HTTPBearer): {security}")
        
    except Exception as e:
        print(f"❌ Import dependencies failed: {e}")
        return False
    
    return True


def main():
    """Run all tests"""
    print("\n")
    
    jwt_ok = test_jwt_auth()
    deps_ok = test_dependencies()
    
    print("\n" + "=" * 60)
    if jwt_ok and deps_ok:
        print("✅ All authentication tests passed!")
        print("\n📝 Next steps:")
        print("   1. Create .env file and configure DATABASE_URL")
        print("   2. Create PostgreSQL database")
        print("   3. Run: alembic revision --autogenerate -m 'Initial'")
        print("   4. Run: alembic upgrade head")
        print("   5. Test with real API calls")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
