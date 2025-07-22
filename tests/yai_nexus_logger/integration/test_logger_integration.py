# tests/yai_nexus_logger/integration/test_logger_integration.py

import logging
import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# 导入新的 get_logger 方法
from yai_nexus_logger import get_logger, init_logging, trace_context


# 创建一个临时的日志文件用于测试
LOG_FILE = Path("tests/temp_integration_test.log")


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown_log_file():
    """在模块级别创建和清理临时日志文件"""
    # 清理可能存在的旧文件
    if LOG_FILE.exists():
        LOG_FILE.unlink()

    yield

    # 清理所有 handler，确保文件句柄被释放
    logging.shutdown()

    # 测试结束后删除日志文件
    if LOG_FILE.exists():
        LOG_FILE.unlink()


def clean_logging_environment():
    """一个辅助函数，确保日志系统处于干净状态"""
    manager = logging.Manager(logging.root)
    manager.loggerDict.clear()
    logging.root.handlers.clear()
    logging.shutdown()


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
    """测试 get_logger 是否能同时正确配置控制台和文件输出"""
    clean_logging_environment()
    env_vars = {
        "LOG_APP_NAME": "integration_test",
        "LOG_LEVEL": "DEBUG",
        "LOG_CONSOLE_ENABLED": "true",
        "LOG_FILE_ENABLED": "true",
        "LOG_FILE_PATH": str(LOG_FILE),
    }

    with patch.dict(os.environ, env_vars, clear=True):
        init_logging()
        logger = get_logger(__name__)

        trace_id = "test-trace-id-123"
        trace_context.set_trace_id(trace_id)

        message = "This is a test message for file and console."
        logger.info(message)

        # 强制刷新所有 handlers，确保日志写入文件
        # 需要获取根 logger 来访问 handlers
        root_logger = logging.getLogger(os.environ["LOG_APP_NAME"])
        for handler in root_logger.handlers:
            handler.flush()

        log_content = read_log_file_content()
        assert message in log_content
        assert trace_id in log_content
        assert "INFO" in log_content
        assert __name__ in log_content


def test_log_level_filtering():
    """测试 LOG_LEVEL 环境变量是否能正确过滤日志"""
    clean_logging_environment()
    env_vars = {
        "LOG_APP_NAME": "level_test",
        "LOG_LEVEL": "WARNING",
        "LOG_FILE_ENABLED": "true",
        "LOG_FILE_PATH": str(LOG_FILE),
    }

    with patch.dict(os.environ, env_vars, clear=True):
        init_logging()
        logger = get_logger(__name__)

        logger.debug("This debug message should NOT be logged.")
        logger.info("This info message should NOT be logged.")
        logger.warning("This warning message SHOULD be logged.")
        logger.error("This error message SHOULD be logged.")

        root_logger = logging.getLogger(os.environ["LOG_APP_NAME"])
        for handler in root_logger.handlers:
            handler.flush()

        log_content = read_log_file_content()
        assert "should NOT be logged" not in log_content
        assert "SHOULD be logged" in log_content
        assert "WARNING" in log_content
        assert "ERROR" in log_content


def test_exception_logging():
    """测试异常信息是否能被正确记录"""
    clean_logging_environment()
    env_vars = {
        "LOG_APP_NAME": "exception_test",
        "LOG_LEVEL": "ERROR",
        "LOG_FILE_ENABLED": "true",
        "LOG_FILE_PATH": str(LOG_FILE),
    }

    with patch.dict(os.environ, env_vars, clear=True):
        init_logging()
        logger = get_logger(__name__)

        try:
            1 / 0
        except ZeroDivisionError:
            logger.error("A division by zero occurred!", exc_info=True)

        root_logger = logging.getLogger(os.environ["LOG_APP_NAME"])
        for handler in root_logger.handlers:
            handler.flush()

        log_content = read_log_file_content()
        assert "A division by zero occurred!" in log_content
        assert "Traceback" in log_content
        assert "ZeroDivisionError: division by zero" in log_content
