from typing import Any, Dict


def get_default_uvicorn_log_config(level: str = "INFO") -> Dict[str, Any]:
    """
    获取 uvicorn 的日志配置。
    此配置将 uvicorn 的访问日志和应用日志重定向到与我们自定义 logger 相同的处理器。

    Args:
        level (str): 日志级别。默认为 "INFO"。

    Returns:
        Dict[str, Any]: uvicorn 的日志配置字典。
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(asctime)s.%(msecs)03d | %(levelname)-7s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(asctime)s.%(msecs)03d | %(levelname)-7s | %(name)s | %(client_addr)s - "%(request_line)s" %(status_code)s',
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "formatter": "default",
                "class": "logging.handlers.TimedRotatingFileHandler",
                "filename": "logs/app.log",
                "when": "midnight",
                "interval": 1,
                "backupCount": 30,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["default", "file"],
                "level": level.upper(),
                "propagate": False,
            },
            "uvicorn.error": {
                "level": level.upper(),
                "handlers": ["default", "file"],
                "propagate": True,
            },
            "uvicorn.access": {
                "handlers": ["access", "file"],
                "level": level.upper(),
                "propagate": False,
            },
        },
    } 