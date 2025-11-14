"""
User Repository
用户数据访问层 - 异步版本
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User


class UserRepository:
    """用户数据仓库"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> User | None:
        """根据ID获取用户"""
        result = await self.db.execute(
            select(User).filter(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_phone(self, phone: str) -> User | None:
        """根据手机号获取用户"""
        result = await self.db.execute(
            select(User).filter(User.phone == phone)
        )
        return result.scalar_one_or_none()
    
    async def create(self, phone: str, hashed_password: str, nickname: Optional[str] = None) -> User:
        """创建新用户"""
        new_user = User(
            phone=phone,
            nickname=nickname or f"用户{phone[-4:]}",
            hashed_password=hashed_password
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user
    
    async def update(self, user: User, **kwargs) -> User:
        """更新用户信息"""
        for field, value in kwargs.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def exists_by_phone(self, phone: str) -> bool:
        """检查手机号是否已注册"""
        result = await self.db.execute(
            select(User).filter(User.phone == phone)
        )
        return result.scalar_one_or_none() is not None
