"""
System Config Repository
系统配置数据访问层
"""
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.system_config import SystemConfig


class SystemConfigRepository:
    """系统配置数据访问"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get(self, config_key: str) -> Optional[Any]:
        """获取配置值"""
        config = self.db.query(SystemConfig).filter(
            SystemConfig.config_key == config_key
        ).first()
        
        return config.config_value if config else None
    
    async def set(self, config_key: str, config_value: Any, description: Optional[str] = None) -> SystemConfig:
        """设置配置值"""
        config = self.db.query(SystemConfig).filter(
            SystemConfig.config_key == config_key
        ).first()
        
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
        config = self.db.query(SystemConfig).filter(
            SystemConfig.config_key == config_key
        ).first()
        
        if not config:
            return False
        
        await self.db.delete(config)
        await self.db.commit()
        return True
    
    async def get_all(self) -> dict:
        """获取所有配置"""
        configs = self.db.query(SystemConfig).all()
        return {config.config_key: config.config_value for config in configs}
