import logging
from typing import Any

from .internal.internal_formatter import InternalFormatter
from .internal.internal_handlers import get_console_handler, get_file_handler

LOGGING_FORMAT = (
    "%(asctime)s.%(msecs)03d | %(levelname)-7s | "
    "%(module)s:%(lineno)d | [%(trace_id)s] | %(message)s"
)


class LoggerBuilder:
    """
    一个采用流式 API 的 logger 构建器。
    """

    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level.upper())
        self.formatter = InternalFormatter(LOGGING_FORMAT)

        # 清除现有处理器，以确保配置是干净的
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # 防止日志向上传递给 root logger
        self.logger.propagate = False

    def with_console_handler(self) -> "LoggerBuilder":
        """添加一个控制台处理器。"""
        handler = get_console_handler(self.formatter)
        self.logger.addHandler(handler)
        return self

    def with_file_handler(
        self,
        path: str = "logs/app.log",
        when: str = "midnight",
        interval: int = 1,
        backup_count: int = 30,
    ) -> "LoggerBuilder":
        """添加一个文件处理器。"""
        handler = get_file_handler(
            self.formatter, path, when, interval, backup_count
        )
        self.logger.addHandler(handler)
        return self

    def build(self) -> logging.Logger:
        """
        构建并返回最终的 logger 实例。
        """
        if not self.logger.handlers:
            # 如果没有配置任何 handler，默认添加控制台输出
            self.with_console_handler()
            
        return self.logger