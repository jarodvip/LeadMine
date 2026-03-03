"""
日志配置 - 使用 loguru 实现结构化日志
"""

import sys
from pathlib import Path
from loguru import logger


def setup_logging():
    """配置日志系统"""
    # 移除默认处理器
    logger.remove()

    # 控制台输出 - 彩色日志
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
    )

    # 文件日志 - 轮转日志
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 应用日志
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        encoding="utf-8",
    )

    # 错误日志单独文件
    logger.add(
        log_dir / "error_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        encoding="utf-8",
    )

    # 设置全局日志级别
    logger.level("INFO")

    return logger


# 初始化日志
app_logger = setup_logging()


def get_logger(name: str = None):
    """获取日志记录器"""
    if name:
        return logger.bind(name=name)
    return logger
