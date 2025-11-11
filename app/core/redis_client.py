"""
Redis Client
Redis客户端封装
"""

import redis
from typing import Optional
from app.core.config import settings


class RedisClient:
    """
    Redis客户端单例
    """
    _instance: Optional[redis.Redis] = None
    
    @classmethod
    def get_client(cls) -> redis.Redis:
        """
        获取Redis客户端实例（单例模式）
        """
        if cls._instance is None:
            cls._instance = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
        return cls._instance
    
    @classmethod
    def close(cls):
        """
        关闭Redis连接
        """
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None


# 便捷函数
def get_redis() -> redis.Redis:
    """
    获取Redis客户端
    用于依赖注入
    """
    return RedisClient.get_client()


# 常用的Redis操作封装
class RedisCache:
    """Redis缓存操作"""
    
    def __init__(self, prefix: str = "timekeeper"):
        self.client = get_redis()
        self.prefix = prefix
    
    def _make_key(self, key: str) -> str:
        """生成带前缀的key"""
        return f"{self.prefix}:{key}"
    
    def get(self, key: str) -> Optional[str]:
        """获取缓存"""
        return self.client.get(self._make_key(key))
    
    def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒），None表示永不过期
        """
        return self.client.set(self._make_key(key), value, ex=expire)
    
    def delete(self, key: str) -> int:
        """删除缓存"""
        return self.client.delete(self._make_key(key))
    
    def exists(self, key: str) -> bool:
        """检查key是否存在"""
        return self.client.exists(self._make_key(key)) > 0
    
    def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        return self.client.expire(self._make_key(key), seconds)
    
    def ttl(self, key: str) -> int:
        """获取剩余过期时间（秒）"""
        return self.client.ttl(self._make_key(key))
    
    def incr(self, key: str, amount: int = 1) -> int:
        """自增"""
        return self.client.incr(self._make_key(key), amount)
    
    def decr(self, key: str, amount: int = 1) -> int:
        """自减"""
        return self.client.decr(self._make_key(key), amount)


# 预定义的缓存实例
user_cache = RedisCache(prefix="user")
reminder_cache = RedisCache(prefix="reminder")
token_cache = RedisCache(prefix="token")
