"""
User Repository - SQLAlchemy 2.0
用户数据访问层
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """用户仓储类 - 使用SQLAlchemy 2.0语法"""
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        根据ID获取用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            用户或None
        """
        stmt = select(User).where(User.id == user_id)
        result = db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    def get_by_phone(db: Session, phone: str) -> Optional[User]:
        """
        根据手机号获取用户
        
        Args:
            db: 数据库会话
            phone: 手机号
            
        Returns:
            用户或None
        """
        stmt = select(User).where(User.phone == phone)
        result = db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    def create(
        db: Session,
        phone: str,
        hashed_password: str,
        nickname: Optional[str] = None
    ) -> User:
        """
        创建用户
        
        Args:
            db: 数据库会话
            phone: 手机号
            hashed_password: 哈希密码
            nickname: 昵称（可选）
            
        Returns:
            创建的用户
        """
        user = User(
            phone=phone,
            hashed_password=hashed_password,
            nickname=nickname or phone[-4:]  # 默认昵称为手机号后4位
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def update(db: Session, user: User, **kwargs) -> User:
        """
        更新用户
        
        Args:
            db: 数据库会话
            user: 用户对象
            **kwargs: 要更新的字段
            
        Returns:
            更新后的用户
        """
        for field, value in kwargs.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def exists_by_phone(db: Session, phone: str) -> bool:
        """
        检查手机号是否已存在
        
        Args:
            db: 数据库会话
            phone: 手机号
            
        Returns:
            是否存在
        """
        stmt = select(User.id).where(User.phone == phone)
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None
