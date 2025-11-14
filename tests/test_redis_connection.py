"""
测试Redis连接
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
import redis

# Load .env
load_dotenv()

def test_redis_connection():
    """Test Redis connection"""
    redis_url = os.getenv('REDIS_URL', 'redis://:123456@localhost:6379/0')
    
    print("="*60)
    print("测试Redis连接")
    print("="*60)
    print(f"\nRedis URL: {redis_url.replace(':123456', ':***')}")
    
    try:
        # Create Redis client
        r = redis.from_url(redis_url, decode_responses=True)
        
        # Test ping
        print("\n[1] 测试PING...")
        response = r.ping()
        print(f"    响应: {response}")
        assert response, "PING失败"
        print("    ✓ PING成功")
        
        # Test set/get
        print("\n[2] 测试SET/GET...")
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        print("    SET: test_key = test_value")
        print(f"    GET: test_key = {value}")
        assert value == 'test_value', "SET/GET失败"
        print("    ✓ SET/GET成功")
        
        # Clean up
        r.delete('test_key')
        
        # Get Redis info
        print("\n[3] Redis信息...")
        info = r.info('server')
        print(f"    版本: {info.get('redis_version', 'unknown')}")
        print(f"    模式: {info.get('redis_mode', 'unknown')}")
        print(f"    端口: {info.get('tcp_port', 'unknown')}")
        
        print("\n" + "="*60)
        print("✅ Redis连接测试通过！")
        print("="*60)
        return True
        
    except redis.ConnectionError as e:
        print(f"\n❌ Redis连接失败: {e}")
        print("\n请检查:")
        print("  1. Redis服务是否启动")
        print("  2. 端口6379是否正确")
        print("  3. 密码是否正确")
        return False
        
    except redis.AuthenticationError as e:
        print(f"\n❌ Redis认证失败: {e}")
        print("\n请检查密码是否正确")
        return False
        
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_redis_connection()
    sys.exit(0 if success else 1)
