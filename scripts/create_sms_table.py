"""
手动创建 sms_logs 表
"""
from app.core.database import engine
from app.models.sms_log import SmsLog
from app.core.database import Base

if __name__ == '__main__':
    # 创建 sms_logs 表
    Base.metadata.create_all(bind=engine, tables=[SmsLog.__table__])
    print("✅ sms_logs 表创建成功!")
