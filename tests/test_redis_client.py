"""
测试Redis客户端封装
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.redis_client import RedisClient, RedisCache, user_cache, reminder_cache


def test_redis_client():
    """测试Redis客户端"""
    print("="*60)
    print("测试Redis客户端封装")
    print("="*60)
    
    # 测试1: 获取客户端
    print("\n[1] 测试获取Redis客户端...")
    client = RedisClient.get_client()
    print(f"    客户端类型: {type(client).__name__}")
    assert client is not None, "客户端不应该为空"
    print("    ✓ 获取客户端成功")
    
    # 测试2: 单例模式
    print("\n[2] 测试单例模式...")
    client2 = RedisClient.get_client()
    assert client is client2, "应该返回相同的实例"
    print("    ✓ 单例模式正确")
    
    # 测试3: PING
    print("\n[3] 测试PING...")
    response = client.ping()
    assert response, "PING应该返回True"
    print("    ✓ PING成功")
    
    # 测试4: RedisCache基本操作
    print("\n[4] 测试RedisCache基本操作...")
    cache = RedisCache(prefix="test")
    
    # SET
    result = cache.set("hello", "world")
    assert result, "SET应该成功"
    print("    ✓ SET成功")
    
    # GET
    value = cache.get("hello")
    assert value == "world", f"GET应该返回'world'，实际返回'{value}'"
    print("    ✓ GET成功")
    
    # EXISTS
    exists = cache.exists("hello")
    assert exists, "key应该存在"
    print("    ✓ EXISTS成功")
    
    # DELETE
    deleted = cache.delete("hello")
    assert deleted > 0, "DELETE应该返回删除数量"
    exists = cache.exists("hello")
    assert not exists, "key应该已被删除"
    print("    ✓ DELETE成功")
    
    # 测试5: 过期时间
    print("\n[5] 测试过期时间...")
    cache.set("expire_test", "value", expire=60)
    ttl = cache.ttl("expire_test")
    assert ttl > 0 and ttl <= 60, f"TTL应该在0-60之间，实际为{ttl}"
    print(f"    TTL: {ttl}秒")
    cache.delete("expire_test")
    print("    ✓ 过期时间设置成功")
    
    # 测试6: 自增/自减
    print("\n[6] 测试自增/自减...")
    cache.set("counter", "0")
    
    # INCR
    value = cache.incr("counter")
    assert value == 1, f"INCR后应该为1，实际为{value}"
    print("    ✓ INCR成功")
    
    value = cache.incr("counter", 5)
    assert value == 6, f"INCR 5后应该为6，实际为{value}"
    print("    ✓ INCR(amount)成功")
    
    # DECR
    value = cache.decr("counter")
    assert value == 5, f"DECR后应该为5，实际为{value}"
    print("    ✓ DECR成功")
    
    cache.delete("counter")
    
    # 测试7: 不同前缀的缓存
    print("\n[7] 测试不同前缀的缓存...")
    user_cache.set("123", "user_data")
    reminder_cache.set("123", "reminder_data")
    
    user_value = user_cache.get("123")
    reminder_value = reminder_cache.get("123")
    
    assert user_value == "user_data", "用户缓存值应该是user_data"
    assert reminder_value == "reminder_data", "提醒缓存值应该是reminder_data"
    print("    ✓ 前缀隔离正确")
    
    # 清理
    user_cache.delete("123")
    reminder_cache.delete("123")
    
    print("\n" + "="*60)
    print("✅ Redis客户端测试全部通过！")
    print("="*60)
    
    return True


if __name__ == "__main__":
    try:
        success = test_redis_client()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
