# tests/yai_nexus_logger/unit/test_sls_handler.py

import logging
from unittest.mock import patch

import pytest

from yai_nexus_logger.internal.internal_formatter import InternalFormatter
from yai_nexus_logger.internal.internal_sls_handler import (
    SLS_SDK_AVAILABLE,
    get_sls_handler,
)

# 如果没有安装 SLS SDK，则跳过此文件中的所有测试
pytestmark = pytest.mark.skipif(
    not SLS_SDK_AVAILABLE, reason="SLS SDK not installed"
)


@pytest.fixture(autouse=True)
def clean_logging_environment():
    """A helper to ensure a clean logging state before each test."""
    # 清除 root logger 的所有 handlers
    logging.root.handlers.clear()
    # 关闭所有现有的 loggers
    logging.shutdown()
    # 确保可以重新配置
    with patch("logging.Logger.hasHandlers", return_value=False):
        yield


# 我们现在模拟 get_sls_handler，这是 get_logger 的直接依赖
@pytest.mark.skipif(not SLS_SDK_AVAILABLE, reason="SLS SDK not installed")
@patch("yai_nexus_logger.internal.internal_sls_handler.QueuedLogHandler")
def test_get_sls_handler_creation(mock_queued_handler):
    """测试 get_sls_handler 函数是否能正确创建一个配置好的 SLS handler"""
    formatter = logging.Formatter()
    mock_handler_instance = mock_queued_handler.return_value

    handler = get_sls_handler(
        formatter=formatter,
        app_name="test_app",
        endpoint="ep",
        access_key_id="id",
        access_key_secret="secret",
        project="proj",
        logstore="log",
    )

    assert handler is mock_handler_instance
    mock_handler_instance.setFormatter.assert_called_with(formatter)
    mock_queued_handler.assert_called_with(
        end_point="ep",
        access_key_id="id",
        access_key="secret",
        project="proj",
        log_store="log",
        topic="test_app"
    )


@pytest.mark.skipif(SLS_SDK_AVAILABLE, reason="SLS SDK is installed")
def test_get_logger_sls_import_error_graceful_fail():
    """在未安装 SLS SDK 时，测试 get_sls_handler 是否会引发 ImportError"""
    with pytest.raises(ImportError, match="aliyun-log-python-sdk is not installed"):
        get_sls_handler(
            formatter=logging.Formatter(),
            app_name="test_app",
            endpoint="ep",
            access_key_id="id",
            access_key_secret="secret",
            project="proj",
            logstore="log",
        )


@pytest.mark.skipif(SLS_SDK_AVAILABLE, reason="SLS SDK is installed")
@patch("yai_nexus_logger.internal.internal_sls_handler.SLS_SDK_AVAILABLE", False)
def test_get_logger_with_sls_handler_sdk_unavailable():
    """测试在没有安装SLS SDK时，尝试使用SLS handler会按预期抛出 ImportError。"""
    with pytest.raises(ImportError, match="aliyun-log-python-sdk is not installed"):
        get_sls_handler(
            formatter=logging.Formatter(),
            app_name="test_app",
            endpoint="fake_endpoint",
            access_key_id="fake_id",
            access_key_secret="fake_secret",
            project="fake_project",
            logstore="fake_logstore",
        )


@patch("yai_nexus_logger.internal.internal_sls_handler.QueuedLogHandler")
@patch("yai_nexus_logger.internal.internal_sls_handler.SLS_SDK_AVAILABLE", True)
def test_get_logger_with_sls_handler(MockQueuedLogHandler):
    """测试 get_sls_handler 能否正确配置并返回一个有效的 handler 实例。"""
    mock_handler_instance = MockQueuedLogHandler.return_value
    formatter = InternalFormatter()

    handler = get_sls_handler(
        formatter=formatter,
        app_name="sls_test_app",
        endpoint="fake_endpoint",
        access_key_id="fake_id",
        access_key_secret="fake_secret",
        project="fake_project",
        logstore="fake_logstore",
    )

    assert handler is mock_handler_instance
    mock_handler_instance.setFormatter.assert_called_with(formatter)
    MockQueuedLogHandler.assert_called_once_with(
        end_point="fake_endpoint",
        access_key_id="fake_id",
        access_key="fake_secret",
        project="fake_project",
        log_store="fake_logstore",
        topic="sls_test_app"
    )

    # 创建一个日志记录并发送
    record = logging.LogRecord(
        "test", logging.INFO, "test", 1, "test message", None, None
    )
    handler.emit(record)

    # 验证 emit 是否被正确调用
    mock_handler_instance.emit.assert_called_once_with(record)
