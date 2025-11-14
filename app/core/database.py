"""
Database Configuration
数据库连接配置 - 异步版本
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

# 将 postgresql:// 替换为 postgresql+asyncpg://
async_database_url = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
)

# Create async database engine
engine: AsyncEngine = create_async_engine(
    async_database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False  # 设置为 True 可以看到 SQL 日志
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()


async def get_db()  -> AsyncGenerator[AsyncSession, None]:
    """
    Async database dependency for FastAPI
    获取异步数据库会话
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
