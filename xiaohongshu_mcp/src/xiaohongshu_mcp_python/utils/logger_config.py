"""
日志配置模块
负责日志系统的初始化和配置
"""

from pathlib import Path
from typing import Optional
from loguru import logger

from ..config import settings


def setup_logger(log_level: Optional[str] = None, log_file: Optional[str] = None) -> None:
    """
    配置日志系统
    
    Args:
        log_level: 日志级别，如果为 None 则使用 settings 中的配置
        log_file: 日志文件路径，如果为 None 则只输出到控制台
    """
    logger.remove()
    
    # 使用传入的级别或 settings 中的级别
    level = log_level or settings.LOG_LEVEL
    
    # 控制台输出
    logger.add(
        lambda msg: print(msg, end=""),
        level=level,
        format=settings.LOG_FORMAT,
        colorize=True,
    )
    
    # 如果设置了日志文件，同时输出到文件
    if log_file or settings.LOG_FILE:
        log_file_path = Path(log_file or settings.LOG_FILE)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 文件日志使用更详细的格式
        logger.add(
            log_file_path,
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} | {message}",
            rotation="10 MB",  # 日志文件轮转：10MB
            retention="7 days",  # 保留7天
            compression="zip",  # 压缩旧日志
            encoding="utf-8",
        )
        
        logger.info(f"日志已配置为同时输出到文件: {log_file_path}")

