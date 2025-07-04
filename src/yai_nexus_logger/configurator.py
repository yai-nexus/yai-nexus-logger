# src/yai_nexus_logger/logger_builder.py

import logging
from typing import List

from .internal.internal_formatter import InternalFormatter
from .internal.internal_handlers import (
    get_console_handler,
    get_file_handler,
)
from .internal.internal_settings import settings
from .internal.internal_sls_handler import SLS_SDK_AVAILABLE, get_sls_handler
from .uvicorn_support import configure_uvicorn_logging

LOGGING_FORMAT = (
    "%(asctime)s.%(msecs)03d | %(levelname)-7s | "
    "%(module)s:%(lineno)d | [%(trace_id)s] | %(message)s"
)


class LoggerConfigurator:
    """
    一个采用流式 API 的 logger 构建器。
    """

    def __init__(self, level: str = "INFO"):
        self._name = settings.APP_NAME
        self._level = level.upper()
        self._handlers: List[logging.Handler] = []
        self._formatter = InternalFormatter(LOGGING_FORMAT)
        self._uvicorn_integration = False

    def with_console_handler(self) -> "LoggerConfigurator":
        self._handlers.append(get_console_handler(self._formatter))
        return self

    def with_file_handler(
        self,
        path: str = "logs/app.log",
        when: str = "midnight",
        interval: int = 1,
        backup_count: int = 30,
    ) -> "LoggerConfigurator":
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
    ) -> "LoggerConfigurator":
        if not SLS_SDK_AVAILABLE:
            raise ImportError(
                "aliyun-log-python-sdk is not installed. "
                "SLS handler cannot be added. "
                "Please run 'pip install yai-nexus-logger[sls]' to install it."
            )

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

    def with_uvicorn_integration(self) -> "LoggerConfigurator":
        self._uvicorn_integration = True
        return self

    def configure(self) -> logging.Logger:
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
