"""
Logging Configuration
统一的日志配置模块
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from app.core.config import settings


def setup_logging():
    """
    配置应用日志系统
    
    特性：
    - 日志文件存放在 logs/ 目录
    - 自动轮转（单文件最大10MB，保留5个备份）
    - 同时输出到控制台和文件
    - 根据环境（开发/生产）设置不同日志级别
    """
    # 创建 logs 目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 确定日志级别
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除现有的处理器（避免重复）
    root_logger.handlers.clear()
    
    # 日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器 - 应用日志
    app_log_file = log_dir / "app.log"
    file_handler = RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 文件处理器 - 错误日志（只记录ERROR及以上级别）
    error_log_file = log_dir / "error.log"
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # 降低第三方库的日志级别
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # 记录日志系统初始化信息
    logger = logging.getLogger(__name__)
    logger.info(f"✅ Logging system initialized (level: {logging.getLevelName(log_level)})")
    logger.info(f"📁 Log directory: {log_dir.absolute()}")
    logger.info(f"📝 Application log: {app_log_file.name}")
    logger.info(f"❌ Error log: {error_log_file.name}")
