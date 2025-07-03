import atexit
import logging
import socket
from typing import Optional

# 全局变量，用于持有 SlsHandler 的实例，以便后续可以关闭它
_sls_handler_instance: Optional[logging.Handler] = None

# 尝试导入 SLS 相关的库
try:
    from aliyun.log import LogClient, LogItem
    from aliyun.log.putlogsrequest import PutLogsRequest

    SLS_SDK_AVAILABLE = True
except ImportError:
    SLS_SDK_AVAILABLE = False


class SLSLogHandler(logging.Handler):
    """
    一个自定义的 logging handler，用于将日志发送到阿里云 SLS 服务。
    """

    def __init__(
        self,
        endpoint: str,
        access_key_id: str,
        access_key_secret: str,
        project: str,
        logstore: str,
        topic: str = "",
        source: str = "",
    ):
        super().__init__()
        if not SLS_SDK_AVAILABLE:
            raise ImportError("SLS dependencies are not installed.")

        self.project = project
        self.logstore = logstore
        self.topic = topic
        # 如果 source 未提供，尝试获取本机IP作为来源
        self.source = source if source else self._get_source_ip()

        self.client = LogClient(endpoint, access_key_id, access_key_secret)

    def _get_source_ip(self) -> str:
        """获取本地 IP 地址作为日志来源"""
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "unknown_source"

    def emit(self, record: logging.LogRecord):
        """
        格式化并发送日志记录。
        """
        try:
            log_item = LogItem(
                timestamp=int(record.created),
                contents=[("message", self.format(record))],
            )
            request = PutLogsRequest(
                project=self.project,
                logstore=self.logstore,
                topic=self.topic,
                source=self.source,
                logitems=[log_item],
            )
            self.client.put_logs(request)
        except Exception:
            self.handleError(record)

    def close(self):
        """
        关闭 handler，这是一个空操作，因为 LogClient 不需要显式关闭。
        """
        super().close()


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
    """
    global _sls_handler_instance
    if not SLS_SDK_AVAILABLE:
        raise ImportError(
            "aliyun-log-python-sdk is not installed. "
            "Please run 'pip install yai-nexus-logger[sls]' to install it."
        )

    handler = SLSLogHandler(
        endpoint=endpoint,
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        project=project,
        logstore=logstore,
        topic=topic or app_name,  # 如果 topic 未提供，使用 app_name
        source=source,
    )
    handler.setFormatter(formatter)

    _sls_handler_instance = handler
    return handler


def _shutdown_sls_handler():
    """
    安全地关闭全局的 SlsHandler 实例。
    该函数通过 atexit 模块注册，在程序退出时自动调用。
    """
    global _sls_handler_instance
    if _sls_handler_instance:
        try:
            _sls_handler_instance.close()
        except Exception as e:
            # 在关闭时遇到问题，只记录下来，不应抛出异常
            logging.warning("Failed to close SLS handler: %s", e)
        finally:
            _sls_handler_instance = None


# 在程序退出时自动调用，以确保 SLS handler 被安全关闭
atexit.register(_shutdown_sls_handler) 