"""
灵活的短信测试脚本 - 支持测试不同号码
Usage: python scripts/test_sms_flexible.py [phone_number]
"""
import sys
import json
from app.services.sms_service import generate_and_store_code, get_sms_service, update_sms_log_status
from app.core.database import SessionLocal
from app.core.config import settings


def test_sms(phone: str):
    """测试指定号码的短信发送"""
    print("\n" + "="*70)
    print(f"📱 短信发送测试 - {phone}")
    print("="*70)
    
    db = SessionLocal()
    
    try:
        # 1. 生成验证码
        print(f"\n[步骤1] 生成验证码...")
        code, log_id = generate_and_store_code(
            phone=phone,
            purpose='register',
            ip_address='127.0.0.1',
            db=db
        )
        print(f"✅ 验证码已生成: {code}")
        print(f"   数据库日志ID: {log_id}")
        
        # 2. 发送短信
        print(f"\n[步骤2] 发送短信到 {phone}...")
        sms = get_sms_service()
        
        # 显示配置
        print(f"   Provider: {settings.SMS_PROVIDER}")
        print(f"   Sign: {settings.SMS_SIGN_NAME}")
        print(f"   Template: {settings.SMS_TEMPLATE_CODE}")
        
        sign_name = settings.SMS_SIGN_NAME or 'TimeKeeper'
        template_code = settings.SMS_TEMPLATE_CODE or '100001'
        template_param = json.dumps({"code": code, "min": "5"})
        
        print(f"\n   调用阿里云API...")
        success = sms.send_sms(phone, sign_name, template_code, template_param)
        
        # 更新数据库状态
        if log_id:
            status = "sent" if success else "failed"
            error_msg = None if success else "发送失败"
            update_sms_log_status(db, log_id, status, error_msg)
        
        if success:
            print(f"\n✅ 短信发送成功!")
            print(f"📱 验证码: {code}")
            print(f"⏰ 有效期: {settings.SMS_CODE_EXPIRE_SECONDS // 60} 分钟")
            return True
        else:
            print(f"\n❌ 短信发送失败")
            return False
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    # 从命令行参数获取手机号，默认使用示例中的测试号码
    default_phone = '18738710275'  # 您示例代码中使用的号码
    phone = sys.argv[1] if len(sys.argv) > 1 else default_phone
    
    print(f"\n🔐 TimeKeeper 短信验证码测试")
    print(f"测试号码: {phone}")
    print(f"环境: {settings.SMS_PROVIDER}")
    
    result = test_sms(phone)
    
    print("\n" + "="*70)
    if result:
        print("✅ 测试完成: 发送成功")
    else:
        print("❌ 测试完成: 发送失败")
    print("="*70)
    
    sys.exit(0 if result else 1)
