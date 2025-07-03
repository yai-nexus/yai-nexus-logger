import io
import logging
import traceback

from src.yai_nexus_logger.formatter import CustomFormatter
from src.yai_nexus_logger.trace import get_trace_id, set_trace_id, reset_trace_id

# 创建一个可复用的测试 logger 设置
def create_test_logger(stream: io.StringIO) -> logging.Logger:
    logger = logging.getLogger(f"formatter_test_{id(stream)}")
    logger.setLevel(logging.DEBUG)
    
    # 使用我们的 formatter
    formatter = CustomFormatter(
        "%(asctime)s | %(levelname)-7s | [%(trace_id)s] | %(message)s"
    )
    
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
    token = set_trace_id("test-id-for-formatter")
    
    logger.info("This is a test message.")
    
    # 获取日志输出并验证
    log_output = log_stream.getvalue()
    assert "[test-id-for-formatter]" in log_output
    
    reset_trace_id(token)


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
    formatter = CustomFormatter()
    
    # 创建一个模拟的 LogRecord
    class MockRecord:
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
            self.trace_id = "-"
            self.stack_info = None
        
        def getMessage(self):
            return self.msg

    # 完整路径
    record = MockRecord("src.app.api.v1.endpoints")
    formatter.format(record)
    assert record.module == "s.a.a.v1.endpoints"

    # 较短的路径
    record = MockRecord("app.services.users")
    assert formatter._abbreviate_module_name(record.module) == "app.services.users"
    
    # 单个模块
    record = MockRecord("main")
    assert formatter._abbreviate_module_name(record.module) == "main" 