# src/yai_nexus_logger/logger_builder.py

import logging
import os
import sys
import threading
import warnings
from typing import List, Optional

from .internal.internal_formatter import InternalFormatter
from .internal.internal_handlers import (
    get_console_handler,
    get_file_handler,
    get_sls_handler,
    SLS_SDK_AVAILABLE,
)
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
        self._handlers.append(get_console_handler(self._formatter))
        return self

    def with_file_handler(
        self,
        path: str = "logs/app.log",
        when: str = "midnight",
        interval: int = 1,
        backup_count: int = 30,
    ) -> "LoggerBuilder":
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

    def with_sls_handler(
        self,
        endpoint: str,
        access_key_id: str,
        access_key_secret: str,
        project: str,
        logstore: str,
        topic: str = None,
        source: str = None,
    ) -> "LoggerBuilder":
        if not SLS_SDK_AVAILABLE:
            warnings.warn(
                "aliyun-log-python-sdk is not installed. "
                "SLS handler won't be added. "
                "Please run 'pip install yai-nexus-logger[sls]' to install it."
            )
            return self

        sls_handler = get_sls_handler(
            formatter=self._formatter,
            app_name=self._name,
            endpoint=endpoint,
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            project=project,
            logstore=logstore,
            topic=topic,
            source=source,
        )
        self._handlers.append(sls_handler)
        return self

    def with_uvicorn_integration(self) -> "LoggerBuilder":
        self._uvicorn_integration = True
        return self

    def build(self) -> logging.Logger:
        logger = logging.getLogger(self._name)
        logger.setLevel(self._level)
        logger.propagate = False

        if logger.hasHandlers():
            logger.handlers.clear()
        
        if not self._handlers:
            self._handlers.append(get_console_handler(self._formatter))

        for handler in self._handlers:
            logger.addHandler(handler)

        if self._uvicorn_integration:
            configure_uvicorn_logging(handlers=self._handlers, level=self._level)

        return logger


_lock = threading.Lock()
_initialized_loggers = {}
_is_configured = False

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取一个 logger 实例。

    整个应用的日志系统只在第一次调用时被配置一次。
    后续的调用将直接返回已配置好的 logger 实例。
    """
    global _is_configured

    app_name = os.getenv("LOG_APP_NAME", "app")

    # 使用锁确保根 logger (app_name) 的配置只执行一次
    with _lock:
        if not _is_configured:
            level = os.getenv("LOG_LEVEL", "INFO")
            builder = LoggerBuilder(name=app_name, level=level)

            if os.getenv("LOG_CONSOLE_ENABLED", "true").lower() == "true":
                builder.with_console_handler()

            if os.getenv("LOG_FILE_ENABLED", "false").lower() == "true":
                file_path = os.getenv("LOG_FILE_PATH", f"logs/{app_name}.log")
                builder.with_file_handler(path=file_path)

            if os.getenv("SLS_ENABLED", "false").lower() == "true":
                required_vars = [
                    "SLS_ENDPOINT",
                    "SLS_ACCESS_KEY_ID",
                    "SLS_ACCESS_KEY_SECRET",
                    "SLS_PROJECT",
                    "SLS_LOGSTORE",
                ]
                missing_vars = [var for var in required_vars if not os.getenv(var)]
                if missing_vars:
                    warnings.warn(
                        f"SLS logging is enabled, but missing env vars: {', '.join(missing_vars)}. "
                        "SLS handler won't be added."
                    )
                else:
                    builder.with_sls_handler(
                        endpoint=os.getenv("SLS_ENDPOINT"),
                        access_key_id=os.getenv("SLS_ACCESS_KEY_ID"),
                        access_key_secret=os.getenv("SLS_ACCESS_KEY_SECRET"),
                        project=os.getenv("SLS_PROJECT"),
                        logstore=os.getenv("SLS_LOGSTORE"),
                        topic=os.getenv("SLS_TOPIC"),
                        source=os.getenv("SLS_SOURCE"),
                    )

            if os.getenv("LOG_UVICORN_INTEGRATION_ENABLED", "false").lower() == "true":
                builder.with_uvicorn_integration()

            # 这会配置名为 `app_name` 的 logger
            builder.build()
            _is_configured = True

    # 如果提供了名称，则创建或获取一个子 logger
    # 否则，返回应用程序的根 logger
    if name:
        # 这样创建的 logger (如 "app.module") 会自动将日志传播到 "app" logger
        logger_name = f"{app_name}.{name}"
    else:
        logger_name = app_name

    return logging.getLogger(logger_name)