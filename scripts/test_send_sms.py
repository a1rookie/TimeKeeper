"""
简单测试脚本：生成短信验证码并验证redis存储行为
使用方法：
    uv run python scripts/test_send_sms.py

注意：不会发送真实短信，除非你在 .env 中配置了阿里云密钥并安装了 aliyun sdk
"""
from app.services.sms_service import generate_and_store_code, verify_code, get_sms_service
from app.core.config import settings


def main():
    phone = '18738710275'
    purpose = 'register'

    # 生成并存储
    code = generate_and_store_code(phone, purpose=purpose)
    print('Generated code:', code)

    # 验证存在
    ok = verify_code(phone, code, purpose=purpose)
    print('Verify immediate:', ok)

    # 再次验证应该失败
    ok2 = verify_code(phone, code, purpose=purpose)
    print('Verify again (should be False):', ok2)

    # 测试发送（如果配置了Aliyun，会尝试发送）
    sms = get_sms_service()
    sign_name = settings.SMS_SIGN_NAME or 'Test'
    template_code = settings.SMS_TEMPLATE_CODE or '100001'
    template_param = '{"code":"%s","min":"5"}' % code
    sent = sms.send_sms(phone, sign_name, template_code, template_param)
    print('Sent (or noop):', sent)


if __name__ == '__main__':
    main()
