"""
System Config Repository
系统配置数据访问层
"""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.system_config import SystemConfig


class SystemConfigRepository:
    """系统配置数据访问"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get(self, config_key: str) -> Any | None:
        """获取配置值"""
        stmt = select(SystemConfig).where(
            SystemConfig.config_key == config_key
        )
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()
        
        return config.config_value if config else None
    
    async def set(self, config_key: str, config_value: Any, description: str | None = None) -> SystemConfig:
        """设置配置值"""
        stmt = select(SystemConfig).where(
            SystemConfig.config_key == config_key
        )
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()
        
        if config:
            config.config_value = config_value
            if description:
                config.description = description
        else:
            config = SystemConfig(
                config_key=config_key,
                config_value=config_value,
                description=description
            )
            self.db.add(config)
        
        await self.db.commit()
        await self.db.refresh(config)
        return config
    
    async def delete(self, config_key: str) -> bool:
        """删除配置"""
        stmt = select(SystemConfig).where(
            SystemConfig.config_key == config_key
        )
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()
        
        if not config:
            return False
        
        await self.db.delete(config)
        await self.db.commit()
        return True
    
    async def get_all(self) -> dict:
        """获取所有配置"""
        stmt = select(SystemConfig)
        result = await self.db.execute(stmt)
        configs = result.scalars().all()
        return {config.config_key: config.config_value for config in configs}
