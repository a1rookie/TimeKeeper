"""
Logging Configuration
统一的日志配置模块 - 使用structlog
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import structlog
from app.core.config import settings


def setup_logging():
    """
    配置应用日志系统
    
    特性：
    - 使用structlog作为结构化日志库
    - 日志文件存放在 logs/ 目录
    - 自动轮转（单文件最大10MB，保留5个备份）
    - 同时输出到控制台和文件
    - 根据环境（开发/生产）设置不同日志级别和格式
    """
    # 创建 logs 目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 确定日志级别
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # ===== 第一步：配置标准logging（structlog会包装它） =====
    
    # 获取根logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除现有的处理器（避免重复）
    root_logger.handlers.clear()
    
    # 日志格式（用于标准logging的handler）
    formatter = logging.Formatter(
        fmt="%(message)s",  # structlog会处理格式化，这里只输出消息
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
    
    # ===== 第二步：配置structlog来包装标准logging =====
    
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,  # 合并上下文变量
            structlog.stdlib.filter_by_level,  # 按日志级别过滤
            structlog.stdlib.add_logger_name,  # 添加logger名称
            structlog.stdlib.add_log_level,  # 添加日志级别
            structlog.stdlib.PositionalArgumentsFormatter(),  # 格式化位置参数
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),  # 添加时间戳
            structlog.processors.StackInfoRenderer(),  # 渲染堆栈信息
            structlog.processors.format_exc_info,  # 格式化异常信息
            structlog.processors.UnicodeDecoder(),  # Unicode解码
            # 开发环境使用彩色输出，生产环境使用JSON
            structlog.dev.ConsoleRenderer() if settings.DEBUG else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),  # 包装标准logging
        cache_logger_on_first_use=True,
    )
    
    # ===== 第三步：使用structlog记录初始化信息 =====
    
    logger = structlog.get_logger(__name__)
    logger.info(
        "logging_initialized",
        level=logging.getLevelName(log_level),
        log_dir=str(log_dir.absolute()),
        app_log=app_log_file.name,
        error_log=error_log_file.name
    )
