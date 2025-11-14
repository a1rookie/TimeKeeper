"""
真实短信发送测试 - 使用阿里云发送到实际手机号
测试号码: 18738078098
"""
import sys
from app.services.sms_service import generate_and_store_code, get_sms_service, update_sms_log_status
from app.core.database import SessionLocal
from app.core.config import settings
import json


def test_real_sms_send():
    """测试真实短信发送"""
    print("\n" + "="*70)
    print("📱 真实短信发送测试")
    print("="*70)
    
    phone = '18738078098'
    purpose = 'register'
    ip = '127.0.0.1'
    
    db = SessionLocal()
    
    try:
        # 1. 生成验证码
        print("\n[步骤1] 生成验证码...")
        code, log_id = generate_and_store_code(
            phone, 
            purpose, 
            ip_address=ip,
            user_agent="Test Script",
            db=db
        )
        print(f"✅ 验证码已生成: {code}")
        print(f"   数据库日志ID: {log_id}")
        
        # 2. 发送短信
        print(f"\n[步骤2] 发送短信到 {phone}...")
        sms = get_sms_service()
        
        # 检查配置
        print(f"   SMS Provider: {settings.SMS_PROVIDER}")
        print(f"   Access Key ID: {settings.ALIYUN_ACCESS_KEY_ID[:10]}..." if settings.ALIYUN_ACCESS_KEY_ID else "   Access Key ID: 未配置")
        print(f"   Sign Name: {settings.SMS_SIGN_NAME}")
        print(f"   Template Code: {settings.SMS_TEMPLATE_CODE}")
        
        sign_name = settings.SMS_SIGN_NAME or 'TimeKeeper'
        template_code = settings.SMS_TEMPLATE_CODE or '100001'
        # 个人测试模式的模板参数格式
        template_param = json.dumps({"code": code, "min": "5"})
        
        print("\n   正在调用阿里云短信接口...")
        print(f"   参数: phone={phone}, sign={sign_name}, template={template_code}")
        
        ok = sms.send_sms(phone, sign_name, template_code, template_param)
        
        # 更新数据库状态
        if log_id:
            status = "sent" if ok else "failed"
            error_msg = None if ok else "发送失败"
            update_sms_log_status(db, log_id, status, error_msg)
        
        if ok:
            print("✅ 短信发送成功!")
            print(f"   请在 {settings.SMS_CODE_EXPIRE_SECONDS} 秒内查收验证码")
            print(f"\n📱 验证码: {code}")
            print(f"   有效期: {settings.SMS_CODE_EXPIRE_SECONDS // 60} 分钟")
            return code
        else:
            print("❌ 短信发送失败")
            return None
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


def test_rate_limit():
    """测试限频机制"""
    print("\n" + "="*70)
    print("⏱️  测试限频机制（60秒冷却）")
    print("="*70)
    
    phone = '18738078098'
    db = SessionLocal()
    
    try:
        print(f"\n尝试再次发送到 {phone} (应该被限频)...")
        code, log_id = generate_and_store_code(
            phone,
            'register',
            ip_address='127.0.0.1',
            db=db
        )
        print("❌ 不应该成功! (限频未生效)")
    except RuntimeError as e:
        print(f"✅ 限频生效: {e}")
    finally:
        db.close()


def show_statistics():
    """显示发送统计"""
    print("\n" + "="*70)
    print("📊 发送统计")
    print("="*70)
    
    from app.repositories.sms_log_repository import SmsLogRepository
    db = SessionLocal()
    
    try:
        sms_repo = SmsLogRepository(db)
        
        phone = '18738078098'
        ip = '127.0.0.1'
        
        phone_count = sms_repo.count_by_phone_today(phone)
        ip_count = sms_repo.count_by_ip_today(ip)
        
        print(f"\n📱 手机号 {phone}:")
        print(f"   今日发送: {phone_count}/{settings.MAX_SMS_PER_PHONE_PER_DAY} 次")
        if phone_count >= settings.MAX_SMS_PER_PHONE_PER_DAY * 0.8:
            print("   ⚠️  警告: 接近每日限制!")
        
        print(f"\n🌐 IP {ip}:")
        print(f"   今日发送: {ip_count}/{settings.MAX_SMS_PER_IP_PER_DAY} 次")
        
        # 查询最近的记录
        latest = sms_repo.get_latest_unverified(phone, 'register')
        if latest:
            print("\n📝 最新记录:")
            print(f"   验证码: {latest.code}")
            print(f"   状态: {latest.status}")
            print(f"   尝试次数: {latest.verify_attempts}/{settings.MAX_VERIFY_ATTEMPTS}")
            print(f"   创建时间: {latest.created_at}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        db.close()


if __name__ == '__main__':
    print("\n" + "🔐 TimeKeeper 短信验证码真实测试")
    print("="*70)
    print("测试号码: 18738078098")
    print(f"环境: {settings.SMS_PROVIDER}")
    print("="*70)
    
    try:
        # 1. 发送真实短信
        code = test_real_sms_send()
        
        if code:
            # 2. 测试限频
            test_rate_limit()
            
            # 3. 显示统计
            show_statistics()
            
            print("\n" + "="*70)
            print("✅ 测试完成!")
            print("="*70)
            print("\n💡 提示:")
            print(f"   1. 请在手机上查收验证码: {code}")
            print(f"   2. 验证码有效期: {settings.SMS_CODE_EXPIRE_SECONDS // 60} 分钟")
            print("   3. 可以在 60 秒后再次测试发送")
            print(f"   4. 每个手机号每天最多 {settings.MAX_SMS_PER_PHONE_PER_DAY} 次\n")
        else:
            print("\n❌ 短信发送失败，请检查配置")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被中断")
        sys.exit(1)
