"""Unit tests for the InternalFormatter."""
import io
import logging

from yai_nexus_logger import trace_context
from yai_nexus_logger.internal.internal_formatter import InternalFormatter


def create_test_logger(stream: io.StringIO) -> logging.Logger:
    """Create a logger for testing that outputs to a given stream."""
    logger = logging.getLogger(f"formatter_test_{id(stream)}")
    logger.setLevel(logging.DEBUG)
    # 使用我们的 formatter，并包含 trace_id 以便测试
    formatter = InternalFormatter("%(module)s | [%(trace_id)s] | %(message)s")
    # 清除旧的 handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    # 添加流处理器以捕获日志
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def test_formatter_injects_trace_id():
    """
    测试 CustomFormatter 是否能自动注入 trace_id。
    """
    log_stream = io.StringIO()
    logger = create_test_logger(log_stream)
    # 设置一个已知的 trace_id
    token = trace_context.set_trace_id("test-id-for-formatter")
    logger.info("This is a test message.")
    # 获取日志输出并验证
    log_output = log_stream.getvalue()
    assert "[test-id-for-formatter]" in log_output
    trace_context.reset_trace_id(token)


def test_formatter_adds_exception_info_to_error_logs():
    """
    测试对于 ERROR 级别的日志，格式化器是否会自动添加异常信息。
    """
    log_stream = io.StringIO()
    logger = create_test_logger(log_stream)
    try:
        raise ValueError("A test exception")
    except ValueError:
        # 使用 exc_info=True 来触发异常格式化
        logger.error("Caught an exception", exc_info=True)
    log_output = log_stream.getvalue()
    # 验证日志中是否包含堆栈跟踪信息
    assert "Traceback (most recent call last):" in log_output
    assert 'raise ValueError("A test exception")' in log_output


def test_formatter_abbreviates_module_name():
    """
    测试模块名缩写功能。
    """
    formatter = InternalFormatter()
    # 创建一个模拟的 LogRecord
    # pylint: disable=too-many-instance-attributes,too-few-public-methods
    class MockRecord:
        """A mock log record for testing."""

        def __init__(self, module):
            self.module = module
            # 添加其他必要的属性
            self.levelname = "INFO"
            self.levelno = logging.INFO
            self.msg = "test"
            self.args = ()
            self.exc_info = None
            self.exc_text = None
            self.name = "test"
            self.stack_info = None
        # pylint: disable=invalid-name
        def getMessage(self):
            """Mimics the original getMessage method."""
            return self.msg

    # 完整路径，包含版本号
    record = MockRecord("src.app.api.v1.endpoints")
    formatter.format(record)
    assert record.module == "s.a.a.v1.endpoints"

    # 另一个例子
    record = MockRecord("a.b.c.d.e.f")
    formatter.format(record)
    assert record.module == "a.b.c.d.e.f"

    # 路径太短，不缩写
    record = MockRecord("app.services.users")
    formatter.format(record)
    assert record.module == "app.services.users"
    # 单个模块，不缩写
    record = MockRecord("main")
    formatter.format(record)
    assert record.module == "main" 