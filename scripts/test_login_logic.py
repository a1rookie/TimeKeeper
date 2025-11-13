"""
直接测试短信验证码登录逻辑（不需要启动API服务）
"""
import sys
from app.core.database import SessionLocal
from app.services.sms_service import generate_and_store_code, verify_code
from app.repositories import get_user_repository
from app.core.security import create_access_token

def test_sms_login_logic():
    """测试短信验证码登录的核心逻辑"""
    print("\n" + "="*70)
    print("📱 短信验证码登录逻辑测试（直接调用）")
    print("="*70)
    
    phone = "18738710275"
    db = SessionLocal()
    
    try:
        # 1. 检查用户是否存在
        print(f"\n[步骤1] 检查用户 {phone} 是否存在...")
        user_repo = get_user_repository(db)
        user = user_repo.get_by_phone(phone)
        
        if not user:
            print(f"❌ 用户不存在")
            return
        
        print(f"✅ 用户存在")
        print(f"   - ID: {user.id}")
        print(f"   - 昵称: {user.nickname}")
        print(f"   - 激活状态: {user.is_active}")
        
        # 2. 生成并发送验证码
        print(f"\n[步骤2] 生成验证码...")
        code, log_id = generate_and_store_code(
            phone=phone,
            purpose='login',
            ip_address='127.0.0.1',
            db=db
        )
        
        print(f"✅ 验证码已生成")
        print(f"   验证码: {code}")
        print(f"   日志ID: {log_id}")
        print(f"   有效期: 5分钟")
        
        # 3. 模拟真实场景：发送短信
        print(f"\n[步骤3] 发送短信...")
        from app.services.sms_service import get_sms_service, update_sms_log_status
        import json
        from app.core.config import settings
        
        sms = get_sms_service()
        sign_name = settings.SMS_SIGN_NAME or 'TimeKeeper'
        template_code = settings.SMS_TEMPLATE_CODE or '100001'
        template_param = json.dumps({"code": code, "min": "5"})
        
        success = sms.send_sms(phone, sign_name, template_code, template_param)
        
        if log_id:
            status = "sent" if success else "failed"
            error_msg = None if success else "发送失败"
            update_sms_log_status(db, log_id, status, error_msg)
        
        if success:
            print(f"✅ 短信发送成功")
            print(f"   请查收手机短信: {phone}")
        else:
            print(f"⚠️  短信发送失败（但验证码仍可用于测试）")
        
        # 4. 验证验证码
        print(f"\n[步骤4] 验证验证码...")
        print(f"   实际验证码: {code}")
        
        # 测试正确的验证码
        is_valid = verify_code(phone, code, purpose='login', db=db)
        
        if is_valid:
            print(f"✅ 验证码验证成功")
            
            # 5. 生成访问令牌
            print(f"\n[步骤5] 生成访问令牌...")
            token = create_access_token(data={"sub": str(user.id)})
            print(f"✅ 令牌生成成功")
            print(f"   Token: {token[:50]}...")
            
            print(f"\n🎉 登录流程完整测试通过！")
            
        else:
            print(f"❌ 验证码验证失败")
        
        # 6. 测试错误的验证码
        print(f"\n[步骤6] 测试错误验证码...")
        wrong_code = "000000"
        is_valid = verify_code(phone, wrong_code, purpose='login', db=db)
        
        if not is_valid:
            print(f"✅ 错误验证码被正确拒绝")
        else:
            print(f"❌ 错误验证码被错误接受")
        
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n" + "="*70)

if __name__ == "__main__":
    print("🔐 TimeKeeper - 短信验证码登录逻辑测试")
    test_sms_login_logic()
