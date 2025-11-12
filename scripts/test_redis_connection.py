"""
Test Redis Connection
测试Redis连接
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from redis import Redis
from app.core.config import settings

print("=" * 70)
print("Testing Redis Connection")
print("=" * 70)

# 从.env读取的配置
print(f"\nRedis URL from config: {settings.REDIS_URL}")

# 测试连接
try:
    redis_client = Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    
    # Ping test
    redis_client.ping()
    print("✅ Redis connection successful!")
    
    # Set/Get test
    test_key = "test:connection"
    test_value = "Hello Redis!"
    redis_client.set(test_key, test_value, ex=10)  # 10秒过期
    retrieved = redis_client.get(test_key)
    print(f"✅ Set/Get test successful: {retrieved}")
    
    # Info test
    info = redis_client.info('server')
    print(f"✅ Redis server version: {info.get('redis_version')}")
    
    # Cleanup
    redis_client.delete(test_key)
    redis_client.close()
    
    print("\n" + "=" * 70)
    print("All Redis tests passed!")
    print("=" * 70)
    
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
    print("\nPlease check:")
    print("1. Redis container is running: docker ps | findstr redis")
    print("2. Redis URL in .env file is correct")
    print("3. Redis password matches container configuration")
