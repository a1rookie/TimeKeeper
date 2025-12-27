"""
User Repository
用户数据访问层 - 异步版本
"""

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
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
    
    async def create(self, phone: str, hashed_password: str, nickname: str | None = None, **extra_fields) -> User:
        """
        创建新用户
        
        Args:
            phone: 手机号
            hashed_password: 密码哈希
            nickname: 昵称（可选）
            **extra_fields: 其他字段（如 registration_ip, registration_user_agent 等）
        """
        new_user = User(
            phone=phone,
            nickname=nickname or f"用户{phone[-4:]}",
            hashed_password=hashed_password,
            **extra_fields
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
    
    # ========== 防刷相关查询 ==========
    
    async def count_registrations_by_ip_today(self, ip_address: str) -> int:
        """统计某个IP今日的注册次数"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.db.execute(
            select(func.count(User.id)).where(
                User.registration_ip == ip_address,
                User.created_at >= today_start
            )
        )
        return result.scalar_one()
    
    async def count_registrations_by_ip_total(self, ip_address: str) -> int:
        """统计某个IP的总注册次数"""
        result = await self.db.execute(
            select(func.count(User.id)).where(
                User.registration_ip == ip_address
            )
        )
        return result.scalar_one()
    
    async def count_registrations_by_ip_since(
        self, 
        ip_address: str, 
        since: datetime
    ) -> int:
        """统计某个IP从指定时间开始的注册次数"""
        result = await self.db.execute(
            select(func.count(User.id)).where(
                User.registration_ip == ip_address,
                User.created_at >= since
            )
        )
        return result.scalar_one()
    
    async def get_recent_users_by_ip(
        self, 
        ip_address: str, 
        limit: int = 10
    ) -> list[User]:
        """获取某个IP最近注册的用户列表"""
        result = await self.db.execute(
            select(User)
            .where(User.registration_ip == ip_address)
            .order_by(desc(User.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_suspicious_ips(
        self,
        days: int,
        min_registrations: int,
        limit: int = 50
    ) -> list[dict]:
        """获取可疑IP列表（注册次数超过阈值）"""
        days_ago = datetime.now() - timedelta(days=days)
        
        result = await self.db.execute(
            select(
                User.registration_ip,
                func.count(User.id).label('registration_count'),
                func.max(User.created_at).label('last_registration'),
                func.min(User.created_at).label('first_registration')
            )
            .where(
                User.registration_ip.isnot(None),
                User.created_at >= days_ago
            )
            .group_by(User.registration_ip)
            .having(func.count(User.id) >= min_registrations)
            .order_by(desc('registration_count'))
            .limit(limit)
        )
        
        return [
            {
                "ip": row.registration_ip,
                "registration_count": row.registration_count,
                "last_registration": row.last_registration,
                "first_registration": row.first_registration
            }
            for row in result.all()
        ]
    
    async def get_recent_registrations(
        self,
        hours: int,
        limit: int = 50
    ) -> list[User]:
        """获取最近N小时的注册用户"""
        since = datetime.now() - timedelta(hours=hours)
        
        result = await self.db.execute(
            select(User)
            .where(User.created_at >= since)
            .order_by(desc(User.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def ban_user(
        self, 
        user_id: int, 
        reason: str
    ) -> User | None:
        """封禁用户"""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        user.is_banned = True
        user.ban_reason = reason
        user.banned_at = datetime.now()
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def unban_user(self, user_id: int) -> User | None:
        """解封用户"""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        user.is_banned = False
        user.ban_reason = None
        user.banned_at = None
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    # ========== 用户状态更新方法 ==========
    
    async def update_last_login(self, user: User, ip_address: str | None = None) -> User:
        """更新用户最后登录信息"""
        user.last_login_at = datetime.now()
        if ip_address:
            user.last_login_ip = ip_address
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update_password(self, user: User, new_hashed_password: str) -> User:
        """更新用户密码"""
        user.hashed_password = new_hashed_password
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update_phone(self, user: User, new_phone: str) -> User:
        """更新用户手机号"""
        user.phone = new_phone
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def deactivate_user(self, user: User) -> User:
        """注销用户（软删除）"""
        user.is_active = False
        await self.db.commit()
        await self.db.refresh(user)
        return user

