import atexit
import logging
import socket
import sys
import traceback
from datetime import datetime
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
        发送日志记录到 SLS，将 LogRecord 的关键字段作为独立的内容字段。
        """
        try:
            # 直接从 trace_context 获取 trace_id
            from ..trace_context import trace_context
            current_trace_id = trace_context.get_trace_id() or "No-Trace-ID"

            # 基础字段
            contents = [
                ("message", record.getMessage()),  # 使用 getMessage() 获取格式化后的消息
                ("level", record.levelname),
                ("logger", record.name),
                ("module", record.module),
                ("function", record.funcName),
                ("line", str(record.lineno)),
                ("process_id", str(record.process)),
                ("thread_id", str(record.thread)),
                ("trace_id", current_trace_id),
            ]

            # 添加 extra 字段
            from .internal_utils import extract_extra_fields
            extra_fields = extract_extra_fields(record)
            for key, value in extra_fields.items():
                contents.append((key, str(value)))

            # 处理异常信息
            if record.exc_info:
                # 直接使用 handler 自身的 formatter 来处理异常，无需创建新实例
                # self.formatter 在 get_sls_handler 中已经被设置
                if self.formatter:
                    exc_text = self.formatter.formatException(record.exc_info)
                else:
                    # 如果没有设置 formatter（主要在测试中），使用基础格式化器
                    formatter = logging.Formatter()
                    exc_text = formatter.formatException(record.exc_info)
                contents.append(("exception", exc_text))

            log_item = LogItem(
                timestamp=int(record.created),
                contents=contents,
            )
            request = PutLogsRequest(
                project=self.project,
                logstore=self.logstore,
                topic=self.topic,
                source=self.source,
                logitems=[log_item],
            )
            self.client.put_logs(request)
        except Exception as e:
            self._handle_emit_error(e, record)

    def _handle_emit_error(self, exception: Exception, record: logging.LogRecord):
        """
        处理日志发送到 SLS 时发生的异常。

        不再静默忽略异常，而是将详细的错误信息输出到 stderr，
        确保即使远程日志发送失败，日志信息也不会丢失。
        """
        error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        # 构建原始日志记录的关键信息
        original_log_info = (
            f"[{record.levelname}] {record.name}:{record.lineno} | "
            f"{getattr(record, 'trace_id', 'NO_TRACE')} | "
            f"{record.getMessage()}"
        )

        # 输出详细的错误信息到 stderr
        error_message = f"""
═══ SLS 日志发送失败 [{error_time}] ═══
异常类型: {type(exception).__name__}
异常信息: {str(exception)}
SLS 配置: project={self.project}, logstore={self.logstore}, topic={self.topic}
原始日志: {original_log_info}
堆栈跟踪:
{traceback.format_exc()}
════════════════════════════════════════════════
"""

        # 输出到 stderr，确保信息不会丢失
        print(error_message, file=sys.stderr, flush=True)


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
