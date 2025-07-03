import logging
import warnings
from typing import Optional

from .configurator import LoggerConfigurator
from .internal.internal_settings import settings


def init_logging(builder: Optional[LoggerConfigurator] = None) -> None:
    """
    初始化应用日志系统。

    此函数应在应用程序启动时显式调用一次。
    如果未提供 builder，将尝试从环境变量进行配置。
    """
    if logging.getLogger(settings.APP_NAME).hasHandlers():
        warnings.warn(
            f"Logger '{settings.APP_NAME}' seems to be already configured. "
            "Skipping initialization."
        )
        return

    if builder:
        builder.configure()
        return

    # 从 settings.py 读取配置并构建 logger
    configurator = LoggerConfigurator(level=settings.LOG_LEVEL)

    if settings.CONSOLE_ENABLED:
        configurator.with_console_handler()

    if settings.FILE_ENABLED:
        configurator.with_file_handler(path=settings.FILE_PATH)

    if settings.SLS_ENABLED:
        required_vars = [
            settings.SLS_ENDPOINT,
            settings.SLS_ACCESS_KEY_ID,
            settings.SLS_ACCESS_KEY_SECRET,
            settings.SLS_PROJECT,
            settings.SLS_LOGSTORE,
        ]
        if any(not var for var in required_vars):
            warnings.warn(
                "SLS logging is enabled, but some required SLS environment "
                "variables are missing. SLS handler won't be added."
            )
        else:
            configurator.with_sls_handler(
                endpoint=settings.SLS_ENDPOINT,
                access_key_id=settings.SLS_ACCESS_KEY_ID,
                access_key_secret=settings.SLS_ACCESS_KEY_SECRET,
                project=settings.SLS_PROJECT,
                logstore=settings.SLS_LOGSTORE,
                topic=settings.SLS_TOPIC,
                source=settings.SLS_SOURCE,
            )

    if settings.UVICORN_INTEGRATION_ENABLED:
        configurator.with_uvicorn_integration()

    configurator.configure()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取一个 logger 实例。

    此函数假设日志系统已通过 init_logging() 初始化，它本身不执行任何配置。
    """
    if name:
        logger_name = f"{settings.APP_NAME}.{name}"
    else:
        logger_name = settings.APP_NAME

    return logging.getLogger(logger_name)
