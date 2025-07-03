import logging

from .formatter import CustomFormatter
from .handler import get_console_handler, get_file_handler

LOGGING_FORMAT = (
    "%(asctime)s.%(msecs)03d | %(levelname)-7s | "
    "%(module)s:%(lineno)d | [%(trace_id)s] | %(message)s"
)


def setup_logger(name: str = "app", level: str = "INFO") -> logging.Logger:
    """
    设置和配置一个 logger。

    这个函数是幂等的：重复调用相同的名称不会导致日志重复。
    它会清除指定 logger 上任何现有的处理器，然后添加新的。

    Args:
        name (str): logger 的名称。默认为 "app"。
        level (str): 日志级别 (e.g., "INFO", "DEBUG")。默认为 "INFO"。

    Returns:
        logging.Logger: 配置好的 logger 实例。
    """
    logger = logging.getLogger(name)
    logger.setLevel(level.upper())
    
    # 清除现有处理器，以确保配置是干净的，并防止日志重复
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = CustomFormatter(LOGGING_FORMAT)

    logger.addHandler(get_console_handler(formatter))
    logger.addHandler(get_file_handler(formatter))

    # 设置 propagate 为 False，防止日志向上传递给 root logger，避免重复输出
    logger.propagate = False

    return logger 