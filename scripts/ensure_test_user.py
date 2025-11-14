"""
检查测试用户是否存在，不存在则创建
"""
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()

phone = "18738710275"
user = db.query(User).filter(User.phone == phone).first()

if user:
    print("\n✅ 测试用户已存在")
    print(f"   ID: {user.id}")
    print(f"   昵称: {user.nickname or 'N/A'}")
    print(f"   手机号: {user.phone}")
    print(f"   状态: {'激活' if user.is_active else '未激活'}")
else:
    print(f"\n⚠️  测试用户不存在: {phone}")
    print("请先使用以下方式之一创建用户：")
    print("\n1. 通过注册API创建（推荐）:")
    print("   POST /api/v1/users/register")
    print(f"   {{'username':'testuser','email':'test@example.com','password':'Test123456','phone':'{phone}','sms_code':'验证码'}}")
    print("\n2. 手动创建（临时测试）:")
    
    create = input("\n是否立即创建测试用户？(y/n): ").strip().lower()
    
    if create == 'y':
        nickname = input("昵称 [测试用户]: ").strip() or "测试用户"
        password = input("密码 [Test123456]: ").strip() or "Test123456"
        
        new_user = User(
            phone=phone,
            nickname=nickname,
            hashed_password=get_password_hash(password),
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print("\n✅ 用户创建成功!")
        print(f"   ID: {new_user.id}")
        print(f"   昵称: {new_user.nickname}")
        print(f"   手机号: {new_user.phone}")
        print(f"   密码: {password}")

db.close()
