"""
完整测试：短信验证码防刷机制
测试项：
1. 正常发送和验证流程
2. 60秒限频测试
3. 验证码尝试次数限制（5次）
4. 每日发送次数限制
"""
import sys
import time
from app.services.sms_service import generate_and_store_code, verify_code
from app.core.redis import get_redis
from app.core.database import SessionLocal
from app.repositories.sms_log_repository import SmsLogRepository


def test_normal_flow():
    """测试1: 正常流程"""
    print("\n" + "="*60)
    print("测试1: 正常发送和验证流程")
    print("="*60)
    
    db = SessionLocal()
    phone = '18738710275'
    purpose = 'register'
    ip = '127.0.0.1'
    
    try:
        # 生成验证码
        code, log_id = generate_and_store_code(phone, purpose, ip_address=ip, db=db)
        print(f"✅ 生成验证码: {code}, log_id: {log_id}")
        
        # 验证成功
        ok = verify_code(phone, code, purpose, db=db)
        print(f"✅ 验证结果: {ok}")
        
        # 再次验证应该失败（已删除）
        ok2 = verify_code(phone, code, purpose, db=db)
        print(f"✅ 二次验证（应该失败）: {ok2}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        db.close()


def test_rate_limit():
    """测试2: 60秒限频"""
    print("\n" + "="*60)
    print("测试2: 60秒限频测试")
    print("="*60)
    
    db = SessionLocal()
    phone = '18738710276'
    purpose = 'register'
    ip = '127.0.0.2'
    
    try:
        # 第一次发送
        code1, log_id1 = generate_and_store_code(phone, purpose, ip_address=ip, db=db)
        print(f"✅ 第一次发送成功: {code1}")
        
        # 立即第二次发送（应该被限频）
        try:
            code2, log_id2 = generate_and_store_code(phone, purpose, ip_address=ip, db=db)
            print(f"❌ 第二次发送不应该成功!")
        except RuntimeError as e:
            print(f"✅ 限频生效: {e}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        db.close()


def test_verify_attempts():
    """测试3: 验证尝试次数限制"""
    print("\n" + "="*60)
    print("测试3: 验证尝试次数限制（5次）")
    print("="*60)
    
    db = SessionLocal()
    phone = '18738710277'
    purpose = 'register'
    ip = '127.0.0.3'
    
    try:
        # 生成验证码
        code, log_id = generate_and_store_code(phone, purpose, ip_address=ip, db=db)
        print(f"✅ 生成验证码: {code}")
        
        # 错误尝试5次
        wrong_code = "000000"
        for i in range(5):
            ok = verify_code(phone, wrong_code, purpose, db=db)
            print(f"   尝试 {i+1}/5: {ok}")
        
        # 第6次应该被阻止
        try:
            ok = verify_code(phone, wrong_code, purpose, db=db)
            print(f"❌ 第6次尝试不应该被允许!")
        except RuntimeError as e:
            print(f"✅ 尝试次数限制生效: {e}")
            
        # 即使用正确的验证码也不行
        try:
            ok = verify_code(phone, code, purpose, db=db)
            print(f"❌ 正确验证码也不应该通过!")
        except RuntimeError as e:
            print(f"✅ 正确验证码也被限制: {e}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        db.close()


def test_daily_limit():
    """测试4: 每日发送次数限制"""
    print("\n" + "="*60)
    print("测试4: 每日发送次数限制检查")
    print("="*60)
    
    db = SessionLocal()
    phone = '18738710278'
    ip = '127.0.0.4'
    
    try:
        sms_repo = SmsLogRepository(db)
        
        # 查询今日发送次数
        count = sms_repo.count_by_phone_today(phone)
        print(f"📊 手机号 {phone} 今日已发送: {count}/10 次")
        
        ip_count = sms_repo.count_by_ip_today(ip)
        print(f"📊 IP {ip} 今日已发送: {ip_count}/50 次")
        
        # 如果接近限制，提示
        if count >= 8:
            print(f"⚠️  警告: 接近每日限制!")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        db.close()


def test_redis_storage():
    """测试5: Redis存储检查"""
    print("\n" + "="*60)
    print("测试5: Redis存储检查")
    print("="*60)
    
    redis = get_redis()
    if not redis:
        print("❌ Redis不可用")
        return
    
    # 检查是否有限频key
    keys = redis.keys("sms:rl:*")
    print(f"📊 当前限频key数量: {len(keys)}")
    for key in keys[:5]:  # 只显示前5个
        ttl = redis.ttl(key)
        print(f"   {key}: 剩余 {ttl}秒")


if __name__ == '__main__':
    print("\n" + "🔒 短信验证码防刷机制测试套件")
    print("="*60)
    
    try:
        test_normal_flow()
        test_rate_limit()
        test_verify_attempts()
        test_daily_limit()
        test_redis_storage()
        
        print("\n" + "="*60)
        print("✅ 所有测试完成!")
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被中断")
        sys.exit(1)
