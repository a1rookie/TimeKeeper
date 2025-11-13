"""
Redis Connection
Redis 连接管理
"""
from typing import Optional
from redis import Redis
from app.core.config import settings

_redis_client: Optional[Redis] = None


def get_redis() -> Optional[Redis]:
    """
    获取Redis客户端
    
    Returns:
        Redis客户端实例，如果连接失败则返回None
    """
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,  # 自动解码为字符串
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 测试连接
            _redis_client.ping()
            print(f"[OK] Redis connected: {settings.REDIS_URL.split('@')[-1]}")
        except Exception as e:
            print(f"[WARN] Redis connection failed: {e}")
            print("   Session management will fallback to JWT only")
            _redis_client = None
    
    return _redis_client


def close_redis():
    """关闭Redis连接"""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None
