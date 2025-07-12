import logging
from typing import Optional

# 尝试导入 SLS 相关的库
try:
    from aliyun.log import QueuedLogHandler

    SLS_SDK_AVAILABLE = True
except ImportError:
    SLS_SDK_AVAILABLE = False




def get_sls_handler(
    formatter: logging.Formatter,
    app_name: str,
    endpoint: str,
    access_key_id: str,
    access_key_secret: str,
    project: str,
    logstore: str,
    topic: Optional[str] = None,
    source: Optional[str] = None,
) -> logging.Handler:
    """
    获取一个阿里云SLS（日志服务）的 handler。
    使用官方的 QueuedLogHandler 实现高性能异步日志处理。
    """
    if not SLS_SDK_AVAILABLE:
        raise ImportError(
            "aliyun-log-python-sdk is not installed. "
            "Please run 'pip install yai-nexus-logger[sls]' to install it."
        )

    handler = QueuedLogHandler(
        end_point=endpoint,
        access_key_id=access_key_id,
        access_key=access_key_secret,
        project=project,
        log_store=logstore,
        topic=topic or app_name,  # 如果 topic 未提供，使用 app_name
    )
    handler.setFormatter(formatter)
    
    # 设置 source（日志来源），如果未提供则使用默认值
    if source:
        handler.source = source
    
    return handler


