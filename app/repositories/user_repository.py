"""
User Repository
用户数据访问层
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    """用户数据仓库"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_phone(self, phone: str) -> Optional[User]:
        """根据手机号获取用户"""
        return self.db.query(User).filter(User.phone == phone).first()
    
    def create(self, phone: str, hashed_password: str, nickname: Optional[str] = None) -> User:
        """创建新用户"""
        new_user = User(
            phone=phone,
            nickname=nickname or f"用户{phone[-4:]}",
            hashed_password=hashed_password
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user
    
    def update(self, user: User, **kwargs) -> User:
        """更新用户信息"""
        for field, value in kwargs.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def exists_by_phone(self, phone: str) -> bool:
        """检查手机号是否已注册"""
        return self.db.query(User).filter(User.phone == phone).first() is not None
