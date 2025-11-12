"""
TimeKeeper Backend Application
周期提醒 APP 后端主应用
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import users, reminders, push_tasks, family, completions, templates
from app.services.push_scheduler import get_scheduler
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    在应用启动时初始化推送调度器，在关闭时停止
    """
    # Startup
    logger.info("Starting TimeKeeper application...")
    
    # 启动推送调度器（如果启用）
    if settings.JPUSH_ENABLED:
        try:
            scheduler = get_scheduler()
            await scheduler.start()
            logger.info("Push scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start push scheduler: {e}")
    else:
        logger.info("Push scheduler disabled (JPUSH_ENABLED=false)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down TimeKeeper application...")
    
    # 停止推送调度器
    if settings.JPUSH_ENABLED:
        try:
            scheduler = get_scheduler()
            await scheduler.stop()
            logger.info("Push scheduler stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop push scheduler: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="周期提醒 APP 后端 API",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/v1")
app.include_router(reminders.router, prefix="/api/v1")
app.include_router(push_tasks.router, prefix="/api/v1")
app.include_router(family.router, prefix="/api/v1/family", tags=["Family"])
app.include_router(completions.router, prefix="/api/v1", tags=["Completions"])
app.include_router(templates.router, prefix="/api/v1", tags=["Templates"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "欢迎使用 TimeKeeper API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
