"""Provides support for integrating the logger with Uvicorn's logging system."""

import logging
from typing import List

try:
    from uvicorn.logging import AccessFormatter
    UVICORN_AVAILABLE = True
except ImportError:
    UVICORN_AVAILABLE = False
    AccessFormatter = None

from yai_nexus_logger.trace_context import trace_context


class UvicornAccessFormatter(logging.Formatter):
    """
    Custom formatter for Uvicorn access logs to include the trace_id.
    It wraps Uvicorn's default AccessFormatter and prepends the trace_id.
    """

    def __init__(self):
        super().__init__()
        self.access_formatter = AccessFormatter()

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the log message to include trace_id and other structured info.
        """
        access_log = self.access_formatter.format(record)

        # Get trace_id from context
        trace_id = trace_context.get_trace_id()
        trace_id_str = f"[{trace_id}]" if trace_id else "[No-Trace-ID]"

        # Our final format
        return f"{trace_id_str} | {access_log}"


def configure_uvicorn_logging(
    handlers: List[logging.Handler], level: str = "INFO"
) -> None:
    """
    为 Uvicorn 的访问日志添加 trace_id 支持。
    只处理控制台输出的访问日志，不强制重定向到文件或 SLS。
    这样既保留了 trace_id 追踪的核心价值，又避免了复杂的 handler 兼容性问题。

    Args:
        handlers (List[logging.Handler]): A list of logging handlers to check for console output.
        level (str): The logging level to set for the Uvicorn access logger.
    """
    if not UVICORN_AVAILABLE:
        return  # Silently skip if uvicorn is not available

    # 只处理 uvicorn.access，为其添加 trace_id 支持
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.handlers.clear()
    uvicorn_access_logger.propagate = False  # Prevent logs from propagating to the root logger

    # 只为 StreamHandler 类型的 handler 添加 trace_id，避免复杂的 handler 兼容性问题
    # 这包括 StreamHandler 和 FileHandler（FileHandler 继承自 StreamHandler）
    # 但排除 QueuedLogHandler 等其他类型的 handler
    stream_handlers = [h for h in handlers if isinstance(h, logging.StreamHandler)]
    for handler in stream_handlers:
        handler_copy = logging.StreamHandler(handler.stream)
        handler_copy.setFormatter(UvicornAccessFormatter())
        uvicorn_access_logger.addHandler(handler_copy)

    uvicorn_access_logger.setLevel(level.upper())

    # 不处理 uvicorn 和 uvicorn.error，让它们保持默认行为
    # 这样可以避免日志混乱，并保持各自的职责分离
