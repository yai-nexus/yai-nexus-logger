# tests/yai_nexus_logger/integration/test_logger_integration.py

import logging
import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# 导入新的 get_logger 方法
from yai_nexus_logger import get_logger, trace_context
from yai_nexus_logger.internal.internal_handlers import (
    _shutdown_sls_handler,  # 导入内部关闭函数
)

# 测试用的日志文件路径
LOG_FILE = Path("tests/examples/logs/integration_test.log")


# 这个 fixture 将在每个测试函数前后自动运行
@pytest.fixture(autouse=True)
def cleanup_log_file_and_context():
    """在每次测试后清理日志文件，并重置 logger 和 trace_context 的配置"""
    # ---- setup ----
    # 在测试开始前先清理配置
    try:
        from yai_nexus_logger import logger_builder
        logger_builder._is_configured = False
        logger_builder._initialized_loggers.clear()
    except (ImportError, AttributeError):
        pass
    
    # 删除可能存在的旧日志文件
    if LOG_FILE.exists():
        os.remove(LOG_FILE)
        
    yield
    # ---- teardown ----
    # 强制关闭可能存在的 SLS 后台线程
    _shutdown_sls_handler()

    # 清理已初始化的 logger，以便下次测试可以重新配置
    try:
        from yai_nexus_logger import logger_builder
        logger_builder._is_configured = False
        logger_builder._initialized_loggers.clear()
    except (ImportError, AttributeError):
        pass

    # 清理 trace_context，防止测试间串扰
    trace_context.clear()

    # 删除测试生成的日志文件
    if LOG_FILE.exists():
        os.remove(LOG_FILE)


def read_log_file_content() -> str:
    """读取并返回日志文件内容"""
    if not LOG_FILE.exists():
        return ""
    # 强制刷新所有handler，确保日志写入文件
    logging.shutdown()
    # 文件IO有延迟，给一小段时间确保写入完成
    time.sleep(0.2)
    return LOG_FILE.read_text()


def test_logger_with_console_and_file():
    """
    测试 get_logger 是否能同时正确配置控制台和文件输出
    """
    env_vars = {
        "LOG_APP_NAME": "integration_test",
        "LOG_LEVEL": "DEBUG",
        "LOG_CONSOLE_ENABLED": "true",
        "LOG_FILE_ENABLED": "true",
        "LOG_FILE_PATH": str(LOG_FILE),
    }

    with patch.dict(os.environ, env_vars):
        logger = get_logger(__name__)
        
        trace_id = "test-trace-id-123"
        trace_context.set_trace_id(trace_id)
        
        message = "This is a test message for file and console."
        logger.info(message)

    # teardown fixture 会在这里运行 logging.shutdown()
    log_content = read_log_file_content()
    assert message in log_content
    assert trace_id in log_content
    assert "INFO" in log_content
    assert __name__ in log_content


def test_log_level_filtering():
    """
    测试 LOG_LEVEL 环境变量是否能正确过滤日志
    """
    env_vars = {
        "LOG_APP_NAME": "level_test",
        "LOG_LEVEL": "WARNING",
        "LOG_FILE_ENABLED": "true",
        "LOG_FILE_PATH": str(LOG_FILE),
    }

    with patch.dict(os.environ, env_vars):
        logger = get_logger(__name__)
        
        logger.debug("This debug message should NOT be logged.")
        logger.info("This info message should NOT be logged.")
        logger.warning("This warning message SHOULD be logged.")
        logger.error("This error message SHOULD be logged.")

    log_content = read_log_file_content()
    assert "should NOT be logged" not in log_content
    assert "SHOULD be logged" in log_content
    assert "WARNING" in log_content
    assert "ERROR" in log_content


def test_exception_logging():
    """
    测试异常信息是否能被正确记录
    """
    env_vars = {
        "LOG_APP_NAME": "exception_test",
        "LOG_LEVEL": "ERROR",
        "LOG_FILE_ENABLED": "true",
        "LOG_FILE_PATH": str(LOG_FILE),
    }

    with patch.dict(os.environ, env_vars):
        logger = get_logger(__name__)
        
        try:
            1 / 0
        except ZeroDivisionError:
            logger.error("A division by zero occurred!", exc_info=True)

    log_content = read_log_file_content()
    assert "A division by zero occurred!" in log_content
    assert "Traceback (most recent call last)" in log_content
    assert "ZeroDivisionError: division by zero" in log_content