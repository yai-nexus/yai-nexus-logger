import logging
import logging.handlers
import sys
from pathlib import Path

LOG_DIR = Path("logs")
# LOG_DIR.mkdir(exist_ok=True) # <-- 移动这行代码


def get_file_handler(formatter: logging.Formatter) -> logging.Handler:
    """
    创建文件处理器，按天轮转日志文件。

    Args:
        formatter: 用于此处理器的日志格式化程序。

    Returns:
        配置好的文件日志处理器。
    """
    # 在创建处理器之前，确保日志目录存在
    LOG_DIR.mkdir(exist_ok=True)

    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=LOG_DIR / "app.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    return file_handler


def get_console_handler(formatter: logging.Formatter) -> logging.Handler:
    """
    创建控制台处理器，将日志输出到 stdout。

    Args:
        formatter: 用于此处理器的日志格式化程序。

    Returns:
        配置好的控制台日志处理器。
    """
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    return console_handler 