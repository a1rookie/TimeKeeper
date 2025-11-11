# Redis配置和使用指南

## 配置说明

### 环境变量配置

在 `.env` 文件中配置Redis连接：

```bash
# Redis连接格式: redis://:password@host:port/db
REDIS_URL=redis://:123456@localhost:6379/0
```

**格式说明：**
- `redis://` - 协议
- `:password` - 密码（注意冒号，无用户名时保留冒号）
- `@localhost` - 主机地址
- `:6379` - 端口号
- `/0` - 数据库编号（0-15）

### 无密码连接

如果Redis没有设置密码：
```bash
REDIS_URL=redis://localhost:6379/0
```

### 有用户名和密码

如果Redis设置了用户名和密码：
```bash
REDIS_URL=redis://username:password@localhost:6379/0
```

## 测试连接

运行测试脚本验证Redis连接：

```bash
python tests/test_redis_connection.py
```

预期输出：
```
✅ Redis连接测试通过！
```

## 使用方法

### 1. 直接使用Redis客户端

```python
from app.core.redis_client import get_redis

# 获取客户端
redis_client = get_redis()

# 基本操作
redis_client.set('key', 'value')
value = redis_client.get('key')
redis_client.delete('key')
```

### 2. 使用封装的缓存类

```python
from app.core.redis_client import RedisCache

# 创建缓存实例
cache = RedisCache(prefix="myapp")

# 设置缓存（永久）
cache.set('user_123', 'user_data')

# 设置缓存（带过期时间）
cache.set('temp_data', 'value', expire=3600)  # 1小时后过期

# 获取缓存
value = cache.get('user_123')

# 检查key是否存在
if cache.exists('user_123'):
    print("Key存在")

# 删除缓存
cache.delete('user_123')

# 获取剩余过期时间（秒）
ttl = cache.ttl('temp_data')

# 自增/自减
cache.set('counter', '0')
cache.incr('counter')        # +1
cache.incr('counter', 10)    # +10
cache.decr('counter')        # -1
```

### 3. 使用预定义的缓存实例

```python
from app.core.redis_client import user_cache, reminder_cache, token_cache

# 用户缓存
user_cache.set('123', 'user_data', expire=3600)
user_data = user_cache.get('123')

# 提醒缓存
reminder_cache.set('456', 'reminder_data')
reminder_data = reminder_cache.get('456')

# Token缓存
token_cache.set('abc123', 'token_data', expire=1800)
```

## 缓存策略建议

### 1. 用户信息缓存

```python
from app.core.redis_client import user_cache
import json

def cache_user_info(user_id: int, user_data: dict, expire: int = 3600):
    """缓存用户信息（1小时）"""
    key = f"info:{user_id}"
    user_cache.set(key, json.dumps(user_data), expire=expire)

def get_cached_user_info(user_id: int) -> dict | None:
    """获取缓存的用户信息"""
    key = f"info:{user_id}"
    data = user_cache.get(key)
    return json.loads(data) if data else None
```

### 2. 接口限流

```python
from app.core.redis_client import RedisCache

rate_limit_cache = RedisCache(prefix="rate_limit")

def check_rate_limit(user_id: int, limit: int = 100, window: int = 60):
    """
    检查速率限制
    
    Args:
        user_id: 用户ID
        limit: 时间窗口内的最大请求数
        window: 时间窗口（秒）
    
    Returns:
        是否允许请求
    """
    key = f"user:{user_id}"
    
    # 获取当前计数
    if not rate_limit_cache.exists(key):
        rate_limit_cache.set(key, "0", expire=window)
    
    count = rate_limit_cache.incr(key)
    
    return count <= limit
```

### 3. 分布式锁

```python
from app.core.redis_client import get_redis
import time

def acquire_lock(lock_name: str, expire: int = 10) -> bool:
    """
    获取分布式锁
    
    Args:
        lock_name: 锁名称
        expire: 过期时间（秒）
    
    Returns:
        是否成功获取锁
    """
    redis_client = get_redis()
    return redis_client.set(f"lock:{lock_name}", "1", nx=True, ex=expire)

def release_lock(lock_name: str):
    """释放分布式锁"""
    redis_client = get_redis()
    redis_client.delete(f"lock:{lock_name}")
```

### 4. 会话管理

```python
from app.core.redis_client import token_cache
import json

def save_session(token: str, session_data: dict, expire: int = 3600):
    """保存会话数据"""
    token_cache.set(token, json.dumps(session_data), expire=expire)

def get_session(token: str) -> dict | None:
    """获取会话数据"""
    data = token_cache.get(token)
    return json.loads(data) if data else None

def delete_session(token: str):
    """删除会话（登出）"""
    token_cache.delete(token)
```

## 性能建议

1. **合理设置过期时间**
   - 用户信息：1小时
   - Token：30分钟
   - 临时数据：5-15分钟

2. **使用前缀隔离数据**
   - 不同业务使用不同前缀
   - 便于批量管理和清理

3. **避免大value**
   - 单个key的value建议不超过10KB
   - 大数据考虑压缩或拆分

4. **批量操作**
   - 使用pipeline减少网络往返
   - 使用mget/mset批量读写

## 监控和维护

### 查看Redis状态

```python
from app.core.redis_client import get_redis

redis_client = get_redis()
info = redis_client.info()

print(f"Redis版本: {info['redis_version']}")
print(f"已用内存: {info['used_memory_human']}")
print(f"连接数: {info['connected_clients']}")
print(f"Key数量: {redis_client.dbsize()}")
```

### 清理过期key

Redis会自动清理过期key，但也可以手动清理：

```python
from app.core.redis_client import RedisCache

cache = RedisCache(prefix="temp")

# 扫描并删除匹配的key
redis_client = get_redis()
for key in redis_client.scan_iter("temp:*"):
    redis_client.delete(key)
```

## 故障处理

### 连接失败

1. 检查Redis服务是否启动
   ```bash
   redis-cli ping
   ```

2. 检查端口和密码
   ```bash
   redis-cli -p 6379 -a 123456 ping
   ```

3. 检查防火墙设置

### 认证失败

确认密码正确，注意URL编码特殊字符：
- `@` → `%40`
- `#` → `%23`
- `/` → `%2F`

### 连接超时

调整超时设置：
```python
redis_client = redis.from_url(
    settings.REDIS_URL,
    socket_connect_timeout=10,  # 连接超时
    socket_timeout=10            # 操作超时
)
```

## 测试

运行所有Redis测试：
```bash
python tests/test_redis_connection.py
python tests/test_redis_client.py
```
