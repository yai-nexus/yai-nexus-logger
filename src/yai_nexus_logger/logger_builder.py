"""A fluent builder for creating and configuring logger instances."""

import logging
from typing import List

from .internal.internal_formatter import InternalFormatter
from .internal.internal_handlers import get_console_handler, get_file_handler
from .uvicorn_support import configure_uvicorn_logging

LOGGING_FORMAT = (
    "%(asctime)s.%(msecs)03d | %(levelname)-7s | "
    "%(module)s:%(lineno)d | [%(trace_id)s] | %(message)s"
)


class LoggerBuilder:
    """
    一个采用流式 API 的 logger 构建器。
    """

    def __init__(self, name: str, level: str = "INFO"):
        self._name = name
        self._level = level.upper()
        self._handlers: List[logging.Handler] = []
        self._formatter = InternalFormatter(LOGGING_FORMAT)
        self._uvicorn_integration = False

    def with_console_handler(self) -> "LoggerBuilder":
        """添加一个控制台处理器。"""
        self._handlers.append(get_console_handler(self._formatter))
        return self

    def with_file_handler(
        self,
        path: str = "logs/app.log",
        when: str = "midnight",
        interval: int = 1,
        backup_count: int = 30,
    ) -> "LoggerBuilder":
        """添加一个文件处理器。"""
        self._handlers.append(
            get_file_handler(
                formatter=self._formatter,
                path=path,
                when=when,
                interval=interval,
                backup_count=backup_count,
            )
        )
        return self

    def with_uvicorn_integration(self) -> "LoggerBuilder":
        """
        Enables integration with Uvicorn, redirecting its logs to our handlers.
        """
        self._uvicorn_integration = True
        return self

    def build(self) -> logging.Logger:
        """
        构建并返回最终的 logger 实例。
        """
        logger = logging.getLogger(self._name)
        logger.setLevel(self._level)
        logger.propagate = False

        # Clear existing handlers to prevent duplicate logs
        if logger.hasHandlers():
            logger.handlers.clear()

        # If no handlers were added, add a default console handler
        if not self._handlers:
            self._handlers.append(get_console_handler(self._formatter))

        for handler in self._handlers:
            logger.addHandler(handler)

        # If Uvicorn integration is enabled, configure its loggers
        if self._uvicorn_integration:
            configure_uvicorn_logging(handlers=self._handlers, level=self._level)

        return logger
