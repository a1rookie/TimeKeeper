"""
查看短信发送记录
"""
from app.core.database import SessionLocal
from app.models.sms_log import SmsLog
from sqlalchemy import desc

db = SessionLocal()

print("\n📊 最近的短信发送记录:")
print("="*80)

logs = db.query(SmsLog).order_by(desc(SmsLog.created_at)).limit(5).all()

for log in logs:
    print(f"\n📱 ID: {log.id}")
    print(f"   手机号: {log.phone}")
    print(f"   用途: {log.purpose}")
    print(f"   状态: {log.status}")
    print(f"   提供商: {log.provider}")
    print(f"   发送时间: {log.sent_at or log.created_at}")
    print(f"   错误信息: {log.error_message or '无'}")
    print(f"   验证尝试: {log.verify_attempts}/{log.is_verified}")

db.close()
print("\n" + "="*80)
