# src/yai_nexus_logger/internal/internal_handlers.py

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def get_console_handler(formatter: logging.Formatter) -> logging.Handler:
    """获取一个控制台输出的 handler"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    return handler


def get_file_handler(
    formatter: logging.Formatter,
    path: str,
    when: str,
    interval: int,
    backup_count: int,
) -> logging.Handler:
    """获取一个文件输出的 handler，支持日志分割"""
    file_path = Path(path)
    # 确保日志文件所在的目录存在
    file_path.parent.mkdir(parents=True, exist_ok=True)

    handler = TimedRotatingFileHandler(
        file_path,
        when=when,
        interval=interval,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setFormatter(formatter)
    return handler
